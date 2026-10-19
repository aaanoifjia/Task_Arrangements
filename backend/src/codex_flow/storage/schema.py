"""SQLite schema migration entry points."""

import sqlite3
from pathlib import Path

MIGRATION_VERSION = 2
_MIGRATION_DIRECTORY = Path(__file__).with_name("migrations")
_MIGRATION_PATHS = {
    1: _MIGRATION_DIRECTORY / "0001_initial.sql",
    2: _MIGRATION_DIRECTORY / "0002_run_controls.sql",
}


def migrate(connection: sqlite3.Connection) -> None:
    """Apply each supported schema migration in order and exactly once."""
    connection.execute("PRAGMA foreign_keys = ON")
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version > MIGRATION_VERSION:
        raise ValueError(f"database schema version {version} is newer than supported")
    while version < MIGRATION_VERSION:
        next_version = version + 1
        try:
            migration_path = _MIGRATION_PATHS[next_version]
        except KeyError as error:
            raise ValueError(f"missing migration for schema version {next_version}") from error
        connection.executescript(migration_path.read_text(encoding="utf-8"))
        connection.execute("DELETE FROM schema_version")
        connection.execute(
            "INSERT INTO schema_version(version, applied_at) VALUES (?, datetime('now'))",
            (next_version,),
        )
        connection.execute(f"PRAGMA user_version = {next_version}")
        connection.commit()
        version = next_version
