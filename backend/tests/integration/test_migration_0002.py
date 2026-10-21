import sqlite3
from pathlib import Path

from codex_flow.storage.schema import MIGRATION_VERSION, migrate


def _columns(connection: sqlite3.Connection) -> set[str]:
    return {row[1] for row in connection.execute("PRAGMA table_info(workflow_runs)")}


def _defaults(connection: sqlite3.Connection) -> dict[str, str | None]:
    return {row[1]: row[4] for row in connection.execute("PRAGMA table_info(workflow_runs)")}


def test_fresh_database_applies_run_control_metadata(tmp_path: Path) -> None:
    connection = sqlite3.connect(tmp_path / "codex-flow.sqlite3")

    migrate(connection)

    assert MIGRATION_VERSION == 3
    assert connection.execute("PRAGMA user_version").fetchone()[0] == 3
    assert {"paused", "paused_at"} <= _columns(connection)
    assert connection.execute("SELECT count(*) FROM schema_version").fetchone()[0] == 1


def test_v1_database_upgrades_to_v2_and_is_idempotent(tmp_path: Path) -> None:
    connection = sqlite3.connect(tmp_path / "codex-flow.sqlite3")
    initial = Path(__file__).parents[2] / "src" / "codex_flow" / "storage" / "migrations" / "0001_initial.sql"
    connection.executescript(initial.read_text(encoding="utf-8"))
    connection.execute(
        "INSERT INTO schema_version(version, applied_at) VALUES (1, datetime('now'))"
    )
    connection.execute("PRAGMA user_version = 1")
    connection.commit()

    migrate(connection)
    migrate(connection)

    assert connection.execute("PRAGMA user_version").fetchone()[0] == 3
    assert {"paused", "paused_at"} <= _columns(connection)
    assert connection.execute("SELECT count(*) FROM schema_version").fetchone()[0] == 1
    assert _defaults(connection)["paused"] == "0"
