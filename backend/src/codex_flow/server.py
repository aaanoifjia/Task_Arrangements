"""Production uvicorn entrypoint for the local desktop/backend service."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from codex_flow.api.app import create_app
from codex_flow.api.config import ServiceConfig


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


def main(argv: Sequence[str] | None = None) -> int:
    """Start the production API server after parsing its explicit options."""
    options = parse_args(argv)
    app = create_app(ServiceConfig.from_db_path(options.db_path))

    import uvicorn

    uvicorn.run(app, host=options.host, port=options.port)
    return 0
