"""SQLite connection setup for the durable local store."""

import sqlite3
from pathlib import Path

from codex_flow.storage.schema import migrate


def open_database(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    migrate(connection)
    return connection
