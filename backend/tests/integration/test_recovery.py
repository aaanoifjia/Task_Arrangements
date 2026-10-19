from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.storage.db import open_database
from codex_flow.storage.recovery import StartupReconciler


async def test_starting_without_thread_fails_closed_and_records_event(tmp_path) -> None:
    connection = open_database(tmp_path / "flow.sqlite3")
    connection.execute("INSERT INTO workflows VALUES ('workflow', 'Workflow', '{}', 'now')")
    connection.execute("INSERT INTO workflow_runs VALUES ('run', 'workflow', '{}', 'RUNNING', 'now')")
    connection.execute("INSERT INTO task_runs(id, workflow_run_id, task_id, status, created_at) VALUES ('task', 'run', 'A', 'STARTING', 'now')")
    connection.commit()

    assert await StartupReconciler(connection, FakeCodexAdapter()).reconcile() == ["task"]
    assert connection.execute("SELECT status FROM task_runs WHERE id = 'task'").fetchone()[0] == "FAILED"
    assert connection.execute("SELECT event_type FROM events").fetchone()[0] == "RECOVERY_REQUIRED_NO_THREAD"


async def test_thread_is_read_but_never_assumed_successful(tmp_path) -> None:
    connection = open_database(tmp_path / "flow.sqlite3")
    connection.execute("INSERT INTO workflows VALUES ('workflow', 'Workflow', '{}', 'now')")
    connection.execute("INSERT INTO workflow_runs VALUES ('run', 'workflow', '{}', 'RUNNING', 'now')")
    connection.execute("INSERT INTO task_runs(id, workflow_run_id, task_id, status, thread_id, created_at) VALUES ('task', 'run', 'A', 'RUNNING', 'thread', 'now')")
    connection.commit()
    adapter = FakeCodexAdapter()

    await StartupReconciler(connection, adapter).reconcile()

    assert adapter.calls == ["read_thread"]
    assert connection.execute("SELECT status FROM task_runs WHERE id = 'task'").fetchone()[0] == "NEEDS_ATTENTION"
