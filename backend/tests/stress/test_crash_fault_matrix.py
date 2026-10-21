from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.storage.db import open_database
from codex_flow.storage.recovery import StartupReconciler

CASES = [
    ("attempt_commit", "STARTING", None, "FAILED"),
    ("thread_creation", "STARTING", None, "FAILED"),
    ("turn_start", "STARTING", None, "FAILED"),
    ("running", "RUNNING", "thread-running", "NEEDS_ATTENTION"),
    ("manual_control", "NEEDS_ATTENTION", "thread-manual", "NEEDS_ATTENTION"),
    ("retry", "STARTING", None, "FAILED"),
    ("continuation", "RUNNING", "thread-continuation", "NEEDS_ATTENTION"),
    ("terminal_persistence", "RUNNING", "thread-terminal", "NEEDS_ATTENTION"),
]


def seed_case(database: Path, status: str, thread_id: str | None) -> None:
    connection = open_database(database)
    connection.execute("INSERT INTO workflows VALUES ('workflow', 'Workflow', '{}', 'now')")
    connection.execute(
        "INSERT INTO workflow_runs(id, workflow_id, snapshot_json, status, created_at, paused, paused_at) "
        "VALUES ('run', 'workflow', '{}', 'RUNNING', 'now', 0, NULL)"
    )
    connection.execute(
        "INSERT INTO task_runs(id, workflow_run_id, task_id, status, thread_id, turn_id, created_at) "
        "VALUES ('parent', 'run', 'A', ?, ?, ?, 'now')",
        (status, thread_id, "turn-1" if thread_id else None),
    )
    connection.execute(
        "INSERT INTO task_runs(id, workflow_run_id, task_id, status, created_at) "
        "VALUES ('child', 'run', 'B', 'BLOCKED', 'now')"
    )
    connection.execute(
        "INSERT INTO attempts(id, task_run_id, status, thread_id, turn_id, created_at) "
        "VALUES ('attempt', 'parent', ?, ?, ?, 'now')",
        (status, thread_id, "turn-1" if thread_id else None),
    )
    connection.commit()
    connection.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("name,status,thread_id,expected_status", CASES)
async def test_crash_fault_matrix_fails_closed_without_duplicate_prompt(
    tmp_path: Path, name: str, status: str, thread_id: str | None, expected_status: str
) -> None:
    database = tmp_path / f"{name}.sqlite3"
    seed_case(database, status, thread_id)
    connection = open_database(database)
    adapter = FakeCodexAdapter()

    assert await StartupReconciler(connection, adapter).reconcile() == ["parent"]
    parent = connection.execute("SELECT status FROM task_runs WHERE id = 'parent'").fetchone()
    child = connection.execute("SELECT status FROM task_runs WHERE id = 'child'").fetchone()
    assert parent["status"] == expected_status
    assert child["status"] == "BLOCKED"
    assert "create_thread" not in adapter.calls
    assert "start_turn" not in adapter.calls
    assert "resume_thread" not in adapter.calls
    assert connection.execute("SELECT count(*) FROM events WHERE task_run_id = 'parent'").fetchone()[0] == 1
