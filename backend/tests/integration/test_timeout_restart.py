from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.domain.status import TaskStatus
from codex_flow.storage.db import open_database
from codex_flow.storage.recovery import StartupReconciler


def seed_timeout_boundary(
    database: Path, *, task_status: TaskStatus, thread_id: str | None, turn_id: str | None
) -> None:
    connection = open_database(database)
    connection.execute("INSERT INTO workflows VALUES ('workflow', 'Workflow', '{}', 'now')")
    connection.execute(
        "INSERT INTO workflow_runs(id, workflow_id, snapshot_json, status, created_at, paused, paused_at) "
        "VALUES ('run', 'workflow', '{}', 'RUNNING', 'now', 0, NULL)"
    )
    connection.execute(
        "INSERT INTO task_runs(id, workflow_run_id, task_id, status, thread_id, turn_id, created_at) "
        "VALUES ('parent', 'run', 'A', ?, ?, ?, 'now')",
        (task_status.value, thread_id, turn_id),
    )
    connection.execute(
        "INSERT INTO task_runs(id, workflow_run_id, task_id, status, created_at) "
        "VALUES ('child', 'run', 'B', 'BLOCKED', 'now')"
    )
    connection.commit()
    connection.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("task_status", "thread_id", "turn_id", "expected_status", "expected_calls"),
    [
        (TaskStatus.STARTING, None, None, TaskStatus.FAILED, []),
        (TaskStatus.RUNNING, "thread-1", "turn-1", TaskStatus.NEEDS_ATTENTION, ["read_thread"]),
    ],
)
async def test_timeout_restart_fails_closed_without_resend_or_release(
    tmp_path: Path,
    task_status: TaskStatus,
    thread_id: str | None,
    turn_id: str | None,
    expected_status: TaskStatus,
    expected_calls: list[str],
) -> None:
    database = tmp_path / f"{task_status.value}.sqlite3"
    seed_timeout_boundary(
        database, task_status=task_status, thread_id=thread_id, turn_id=turn_id
    )
    connection = open_database(database)
    adapter = FakeCodexAdapter()

    assert await StartupReconciler(connection, adapter).reconcile() == ["parent"]
    rows = {
        str(row["task_id"]): row
        for row in connection.execute("SELECT * FROM task_runs WHERE workflow_run_id = 'run'")
    }
    assert rows["A"]["status"] == expected_status.value
    assert rows["B"]["status"] == TaskStatus.BLOCKED.value
    assert adapter.calls == expected_calls
    assert "create_thread" not in adapter.calls
    assert "start_turn" not in adapter.calls
    assert "resume_thread" not in adapter.calls
