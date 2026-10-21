import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.storage.db import open_database
from codex_flow.storage.recovery import StartupReconciler


@pytest.mark.parametrize(
    ("crash_point", "status", "thread_id", "expected"),
    [
        ("after_attempt_commit_before_codex", "STARTING", None, "FAILED"),
        ("after_thread_created_before_save", "STARTING", None, "FAILED"),
        ("after_turn_started_before_save", "STARTING", None, "FAILED"),
        ("while_running", "RUNNING", "thread", "NEEDS_ATTENTION"),
        ("after_terminal_before_success_persisted", "RUNNING", "thread", "NEEDS_ATTENTION"),
    ],
)
async def test_crash_recovery_never_resends_prompt_or_releases_downstream(
    tmp_path, crash_point: str, status: str, thread_id: str | None, expected: str
) -> None:
    connection = open_database(tmp_path / f"{crash_point}.sqlite3")
    connection.execute("INSERT INTO workflows VALUES ('workflow', 'Workflow', '{}', 'now')")
    connection.execute(
        "INSERT INTO workflow_runs(id, workflow_id, snapshot_json, status, created_at, paused, paused_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("run", "workflow", "{}", "RUNNING", "now", 0, None),
    )
    connection.execute(
        "INSERT INTO task_runs(id, workflow_run_id, task_id, status, thread_id, created_at) VALUES ('parent', 'run', 'A', ?, ?, 'now')",
        (status, thread_id),
    )
    connection.execute(
        "INSERT INTO task_runs(id, workflow_run_id, task_id, status, created_at) VALUES ('child', 'run', 'B', 'BLOCKED', 'now')"
    )
    connection.commit()
    adapter = FakeCodexAdapter()

    await StartupReconciler(connection, adapter).reconcile()

    assert "create_thread" not in adapter.calls
    assert "start_turn" not in adapter.calls
    assert connection.execute("SELECT status FROM task_runs WHERE id = 'parent'").fetchone()[0] == expected
    assert connection.execute("SELECT status FROM task_runs WHERE id = 'child'").fetchone()[0] == "BLOCKED"
    assert connection.execute("SELECT count(*) FROM events WHERE task_run_id = 'parent'").fetchone()[0] == 1
