"""SQLite schema migration entry points."""

import sqlite3
from pathlib import Path

MIGRATION_VERSION = 1
_MIGRATION_PATH = Path(__file__).with_name("migrations") / "0001_initial.sql"


def migrate(connection: sqlite3.Connection) -> None:
    """Apply the frozen initial schema exactly once."""
    connection.execute("PRAGMA foreign_keys = ON")
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version > MIGRATION_VERSION:
        raise ValueError(f"database schema version {version} is newer than supported")
    if version == MIGRATION_VERSION:
        return
    connection.executescript(_MIGRATION_PATH.read_text(encoding="utf-8"))
    connection.execute(
        "INSERT INTO schema_version(version, applied_at) VALUES (?, datetime('now'))",
        (MIGRATION_VERSION,),
    )
    connection.execute(f"PRAGMA user_version = {MIGRATION_VERSION}")
    connection.commit()
