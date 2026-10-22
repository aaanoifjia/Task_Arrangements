"""Production uvicorn entrypoint for the local desktop/backend service."""

from __future__ import annotations

import argparse
import ipaddress
import json
import logging
import os
import re
import socket
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI

from codex_flow.api.app import create_app
from codex_flow.api.config import ServiceConfig

BACKEND_VERSION = "0.1.0"
LOG_FILE_NAME = "backend.log"
LOG_MAX_BYTES = 1_048_576
LOG_BACKUP_COUNT = 3
SERVER_LOGGER_NAME = "codex_flow.server"
_REDACTION_PATTERNS = (
    re.compile(r"(?i)(\b(?:authorization\s*:\s*bearer|bearer)\s+)[^\s,;]+"),
    re.compile(
        r"(?i)(\b(?:token|password|secret|api[_-]?key|access[_-]?token)\s*[=:]\s*)[^\s,;&]+"
    ),
    re.compile(r"(?i)(\bprompt\s*[=:]\s*).*$"),
)


@dataclass(frozen=True)
class ServerOptions:
    """Explicit process options accepted by the production entrypoint."""

    host: str
    port: int
    db_path: Path
    token: str | None
    log_dir: Path | None


def build_parser() -> argparse.ArgumentParser:
    """Build the server argument parser without starting any resources."""
    parser = argparse.ArgumentParser(prog="codex-flow-server")
    parser.add_argument("--version", action="version", version=BACKEND_VERSION)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--db",
        "--db-path",
        dest="db_path",
        type=Path,
        default=Path(".codex-flow.sqlite3"),
    )
    parser.add_argument("--token", default=None)
    parser.add_argument("--log-dir", type=Path, default=None)
    return parser


def parse_args(argv: Sequence[str] | None = None) -> ServerOptions:
    """Parse explicit server options without importing or starting uvicorn."""
    arguments = build_parser().parse_args(argv)
    return ServerOptions(
        host=arguments.host,
        port=arguments.port,
        db_path=arguments.db_path,
        token=arguments.token,
        log_dir=arguments.log_dir,
    )


def validate_bind_host(host: str, *, desktop_mode: bool = True) -> None:
    """Reject non-loopback addresses when the service runs in desktop mode."""
    if not desktop_mode:
        return
    try:
        address = ipaddress.ip_address(host)
    except ValueError as error:
        raise ValueError("desktop mode requires an IPv4 or IPv6 loopback host") from error
    if not address.is_loopback:
        raise ValueError("desktop mode requires a loopback bind host")


def readiness_line(port: int, *, pid: int | None = None) -> str:
    """Return the single machine-readable post-bind readiness record."""
    record = {
        "event": "ready",
        "version": BACKEND_VERSION,
        "port": port,
        "pid": pid if pid is not None else os.getpid(),
    }
    return json.dumps(record, separators=(",", ":"))


def emit_readiness(port: int, *, pid: int | None = None) -> None:
    """Write and flush the readiness record without exposing the token."""
    sys.stdout.write(f"{readiness_line(port, pid=pid)}\n")
    sys.stdout.flush()


def redact_log_message(message: str) -> str:
    """Remove bearer/query credentials and prompt contents from diagnostics."""
    redacted = message
    for pattern in _REDACTION_PATTERNS:
        redacted = pattern.sub(r"\1[REDACTED]", redacted)
    return redacted


class RedactingFormatter(logging.Formatter):
    """Format records only after applying the local secret-redaction policy."""

    def format(self, record: logging.LogRecord) -> str:
        return redact_log_message(super().format(record))


def configure_logging(log_dir: Path | None) -> logging.Logger:
    """Configure bounded file-only logging without exposing process credentials."""
    logger = logging.getLogger(SERVER_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    for handler in list(logger.handlers):
        if handler.name == SERVER_LOGGER_NAME:
            logger.removeHandler(handler)
            handler.close()
    if log_dir is None:
        return logger
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        log_dir / LOG_FILE_NAME,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.name = SERVER_LOGGER_NAME
    handler.setFormatter(RedactingFormatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger


def log_startup(logger: logging.Logger, options: ServerOptions) -> None:
    """Record non-secret startup context; the bearer token is intentionally omitted."""
    logger.info(
        "server starting host=%s port=%d db_path=%s log_dir=%s",
        options.host,
        options.port,
        options.db_path,
        options.log_dir,
    )


def _run_server(app: FastAPI, options: ServerOptions) -> None:
    import uvicorn

    class HandshakeServer(uvicorn.Server):
        async def startup(self, sockets: list[socket.socket] | None = None) -> None:
            await super().startup(sockets=sockets)
            if not self.servers:
                raise RuntimeError("uvicorn did not expose a bound server socket")
            bound_sockets = self.servers[0].sockets
            if not bound_sockets:
                raise RuntimeError("uvicorn did not expose a bound server socket")
            emit_readiness(int(bound_sockets[0].getsockname()[1]))

    config = uvicorn.Config(app, host=options.host, port=options.port)
    HandshakeServer(config).run()


def main(argv: Sequence[str] | None = None) -> int:
    """Start the production API server after parsing its explicit options."""
    options = parse_args(argv)
    validate_bind_host(options.host)
    logger = configure_logging(options.log_dir)
    log_startup(logger, options)
    app = create_app(
        ServiceConfig.from_db_path(
            options.db_path,
            token=options.token,
            desktop_mode=options.token is not None,
        )
    )
    _run_server(app, options)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
