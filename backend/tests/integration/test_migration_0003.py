import sqlite3
from pathlib import Path

from codex_flow.storage.schema import MIGRATION_VERSION, migrate

MIGRATIONS = Path(__file__).parents[2] / "src" / "codex_flow" / "storage" / "migrations"
EXPECTED_INDEXES = {
    "idx_workflow_runs_workflow_status",
    "idx_task_runs_run_status",
    "idx_attempts_task",
    "idx_events_run_created_id",
}
MIGRATION_NAMES = {1: "initial", 2: "run_controls", 3: "query_indexes"}


def _index_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'index' AND name LIKE 'idx_%'"
    )
    return {str(row[0]) for row in rows}


def _apply_version(connection: sqlite3.Connection, version: int) -> None:
    for number in range(1, version + 1):
        migration = MIGRATIONS / f"{number:04d}_{MIGRATION_NAMES[number]}.sql"
        connection.executescript(migration.read_text(encoding="utf-8"))
    connection.execute(f"PRAGMA user_version = {version}")
    connection.commit()


def test_fresh_database_applies_query_indexes(tmp_path: Path) -> None:
    connection = sqlite3.connect(tmp_path / "fresh.sqlite3")

    migrate(connection)

    assert MIGRATION_VERSION == 3
    assert connection.execute("PRAGMA user_version").fetchone()[0] == 3
    assert EXPECTED_INDEXES <= _index_names(connection)


def test_v1_and_v2_databases_upgrade_to_v3_idempotently(tmp_path: Path) -> None:
    for version in (1, 2):
        connection = sqlite3.connect(tmp_path / f"v{version}.sqlite3")
        _apply_version(connection, version)

        migrate(connection)
        migrate(connection)

        assert connection.execute("PRAGMA user_version").fetchone()[0] == 3
        assert EXPECTED_INDEXES <= _index_names(connection)


def test_query_plans_use_declared_indexes(tmp_path: Path) -> None:
    connection = sqlite3.connect(tmp_path / "plans.sqlite3")
    migrate(connection)

    plans = {
        "workflow_runs": connection.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM workflow_runs WHERE workflow_id = ? AND status = ?",
            ("workflow", "RUNNING"),
        ).fetchall(),
        "task_runs": connection.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM task_runs WHERE workflow_run_id = ? AND status = ?",
            ("run", "READY"),
        ).fetchall(),
        "attempts": connection.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM attempts WHERE task_run_id = ?",
            ("task",),
        ).fetchall(),
        "events": connection.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM events WHERE workflow_run_id = ? ORDER BY created_at, id",
            ("run",),
        ).fetchall(),
    }

    details = {name: " ".join(str(row[3]) for row in rows) for name, rows in plans.items()}
    assert "idx_workflow_runs_workflow_status" in details["workflow_runs"]
    assert "idx_task_runs_run_status" in details["task_runs"]
    assert "idx_attempts_task" in details["attempts"]
    assert "idx_events_run_created_id" in details["events"]
