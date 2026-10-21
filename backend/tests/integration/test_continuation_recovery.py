from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.storage.db import open_database
from codex_flow.storage.recovery import StartupReconciler


def seed_continuation_crash(
    database_path: Path,
    *,
    task_status: str,
    thread_id: str | None,
    turn_id: str | None,
) -> None:
    connection = open_database(database_path)
    connection.execute("INSERT INTO workflows VALUES ('workflow', 'Workflow', '{}', 'now')")
    connection.execute(
        "INSERT INTO workflow_runs(id, workflow_id, snapshot_json, status, created_at, paused, paused_at) "
        "VALUES ('run', 'workflow', '{}', 'RUNNING', 'now', 0, NULL)"
    )
    connection.execute(
        "INSERT INTO task_runs(id, workflow_run_id, task_id, status, thread_id, turn_id, created_at) "
        "VALUES ('parent', 'run', 'A', ?, ?, ?, 'now')",
        (task_status, thread_id, turn_id),
    )
    connection.execute(
        "INSERT INTO task_runs(id, workflow_run_id, task_id, status, created_at) "
        "VALUES ('child', 'run', 'B', 'BLOCKED', 'now')"
    )
    connection.execute(
        "INSERT INTO attempts(id, task_run_id, status, thread_id, turn_id, created_at) "
        "VALUES ('attempt', 'parent', ?, ?, ?, 'now')",
        (task_status, thread_id, turn_id),
    )
    connection.commit()
    connection.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("crash_point", "task_status", "thread_id", "turn_id", "expected_status", "expected_event"),
    [
        ("before_resume", "STARTING", None, None, "FAILED", "RECOVERY_REQUIRED_NO_THREAD"),
        ("after_resume_before_turn", "STARTING", None, None, "FAILED", "RECOVERY_REQUIRED_NO_THREAD"),
        ("after_turn_start_before_ref_persist", "STARTING", None, None, "FAILED", "RECOVERY_REQUIRED_NO_THREAD"),
        (
            "after_refs_before_terminal",
            "RUNNING",
            "source-thread",
            "continuation-turn",
            "NEEDS_ATTENTION",
            "RECOVERY_THREAD_REQUIRES_RECONCILIATION",
        ),
    ],
)
async def test_continuation_crash_points_fail_closed_without_resending_prompt(
    tmp_path: Path,
    crash_point: str,
    task_status: str,
    thread_id: str | None,
    turn_id: str | None,
    expected_status: str,
    expected_event: str,
) -> None:
    database_path = tmp_path / f"{crash_point}.sqlite3"
    seed_continuation_crash(
        database_path,
        task_status=task_status,
        thread_id=thread_id,
        turn_id=turn_id,
    )
    connection = open_database(database_path)
    adapter = FakeCodexAdapter()

    reconciled = await StartupReconciler(connection, adapter).reconcile()

    assert reconciled == ["parent"]
    assert connection.execute("SELECT status FROM task_runs WHERE id = 'parent'").fetchone()[0] == expected_status
    assert connection.execute("SELECT status FROM task_runs WHERE id = 'child'").fetchone()[0] == "BLOCKED"
    assert connection.execute("SELECT event_type FROM events").fetchone()[0] == expected_event
    assert "create_thread" not in adapter.calls
    assert "resume_thread" not in adapter.calls
    assert "start_turn" not in adapter.calls
    if thread_id is None:
        assert adapter.calls == []
    else:
        assert adapter.calls == ["read_thread"]
