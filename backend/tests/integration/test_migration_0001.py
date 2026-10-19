import sqlite3

from codex_flow.storage.schema import MIGRATION_VERSION, migrate


def test_migration_creates_frozen_tables_and_enables_foreign_keys(tmp_path) -> None:
    connection = sqlite3.connect(tmp_path / "codex-flow.sqlite3")

    migrate(connection)

    tables = {
        row[0]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    assert {
        "schema_version", "workflows", "tasks", "edges", "workflow_runs", "task_runs",
        "attempts", "events", "settings",
    } <= tables
    assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert connection.execute("PRAGMA user_version").fetchone()[0] == MIGRATION_VERSION


def test_migration_is_idempotent(tmp_path) -> None:
    connection = sqlite3.connect(tmp_path / "codex-flow.sqlite3")

    migrate(connection)
    migrate(connection)

    assert connection.execute("SELECT count(*) FROM schema_version").fetchone()[0] == 1
