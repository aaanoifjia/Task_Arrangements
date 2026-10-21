import json
from logging.handlers import RotatingFileHandler
from pathlib import Path

from codex_flow.server import (
    LOG_BACKUP_COUNT,
    LOG_FILE_NAME,
    LOG_MAX_BYTES,
    configure_logging,
    emit_readiness,
    log_startup,
    parse_args,
)


def test_logging_writes_bounded_file_without_token(tmp_path: Path) -> None:
    token = "secret-session-token"
    logger = configure_logging(tmp_path)
    options = parse_args(
        [
            "--token",
            token,
            "--db-path",
            str(tmp_path / "codex-flow.sqlite3"),
            "--log-dir",
            str(tmp_path),
        ]
    )

    log_startup(logger, options)
    for handler in logger.handlers:
        handler.flush()

    log_path = tmp_path / LOG_FILE_NAME
    assert log_path.exists()
    content = log_path.read_text(encoding="utf-8")
    assert "server starting" in content
    assert token not in content
    handler = next(handler for handler in logger.handlers if isinstance(handler, RotatingFileHandler))
    assert handler.maxBytes == LOG_MAX_BYTES
    assert handler.backupCount == LOG_BACKUP_COUNT


def test_readiness_stdout_remains_one_machine_readable_line(
    capsys,
    tmp_path: Path,
) -> None:
    configure_logging(tmp_path).info("file-only log")
    emit_readiness(43127, pid=7124)

    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {
        "event": "ready",
        "version": "0.1.0",
        "port": 43127,
        "pid": 7124,
    }
    assert captured.err == ""
