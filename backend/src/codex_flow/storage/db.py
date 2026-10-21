"""SQLite connection setup for the durable local store."""

import sqlite3
from pathlib import Path

from codex_flow.storage.schema import migrate

SQLITE_BUSY_TIMEOUT_MS = 5_000


def open_database(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=SQLITE_BUSY_TIMEOUT_MS / 1_000)
    connection.row_factory = sqlite3.Row
    connection.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    migrate(connection)
    return connection
