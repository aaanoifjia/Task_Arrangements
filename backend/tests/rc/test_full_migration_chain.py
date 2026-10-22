"""Fresh and historical SQLite migration rehearsal for M11."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from codex_flow.storage.schema import MIGRATION_VERSION, migrate

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS = REPOSITORY_ROOT / "backend" / "src" / "codex_flow" / "storage" / "migrations"


def _seed_historical_database(connection: sqlite3.Connection, version: int) -> None:
    connection.executescript((MIGRATIONS / "0001_initial.sql").read_text(encoding="utf-8"))
    connection.execute("INSERT INTO schema_version(version, applied_at) VALUES (1, 'seed')")
    connection.execute("PRAGMA user_version = 1")
    if version >= 2:
        connection.executescript((MIGRATIONS / "0002_run_controls.sql").read_text(encoding="utf-8"))
        connection.execute("DELETE FROM schema_version")
        connection.execute("INSERT INTO schema_version(version, applied_at) VALUES (2, 'seed')")
        connection.execute("PRAGMA user_version = 2")
    if version >= 3:
        connection.executescript((MIGRATIONS / "0003_query_indexes.sql").read_text(encoding="utf-8"))
        connection.execute("DELETE FROM schema_version")
        connection.execute("INSERT INTO schema_version(version, applied_at) VALUES (3, 'seed')")
        connection.execute("PRAGMA user_version = 3")
    connection.execute("INSERT INTO workflows VALUES ('historical', 'Historical', '{}', 'seed')")
    connection.commit()


@pytest.mark.parametrize("starting_version", [None, 1, 2, 3], ids=["fresh", "v1", "v2", "v3"])
def test_full_migration_chain_reopens_idempotently(
    tmp_path: Path,
    starting_version: int | None,
) -> None:
    database_path = tmp_path / f"migration-{starting_version or 'fresh'}.sqlite3"
    connection = sqlite3.connect(database_path)
    if starting_version is None:
        migrate(connection)
    else:
        _seed_historical_database(connection, starting_version)
        migrate(connection)
    connection.close()

    reopened = sqlite3.connect(database_path)
    try:
        migrate(reopened)
        migrate(reopened)
        assert MIGRATION_VERSION == 3
        assert reopened.execute("PRAGMA user_version").fetchone()[0] == MIGRATION_VERSION
        assert reopened.execute("SELECT count(*) FROM schema_version").fetchone()[0] == 1
        columns = {row[1] for row in reopened.execute("PRAGMA table_info(workflow_runs)")}
        assert {"paused", "paused_at"} <= columns
        index_names = {row[1] for row in reopened.execute("PRAGMA index_list(workflow_runs)")}
        assert "idx_workflow_runs_workflow_status" in index_names
        if starting_version is not None:
            assert reopened.execute("SELECT name FROM workflows WHERE id = 'historical'").fetchone()[0] == "Historical"
    finally:
        reopened.close()
