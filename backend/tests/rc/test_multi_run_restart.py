"""Isolation checks for multiple durable workflow runs after restart."""

from __future__ import annotations

from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexThreadRef, CodexThreadSnapshot
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.storage.db import open_database
from codex_flow.storage.recovery import StartupReconciler
from codex_flow.storage.repositories import StorageRepositories


class TrackingReadAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.read_thread_ids: list[str] = []

    async def read_thread(self, thread: CodexThreadRef) -> CodexThreadSnapshot:
        self.read_thread_ids.append(thread.thread_id)
        return await super().read_thread(thread)


def _workflow(workflow_id: str, task_id: str = "A") -> WorkflowDefinition:
    return WorkflowDefinition(
        id=workflow_id,
        name=workflow_id,
        tasks=[TaskDefinition(id=task_id, name=task_id, prompt=workflow_id, cwd=".")],
        edges=[],
    )


@pytest.mark.asyncio
async def test_multiple_runs_reopen_independently_without_identity_mixup(tmp_path: Path) -> None:
    database_path = tmp_path / "multi-run.sqlite3"
    connection = open_database(database_path)
    repository = StorageRepositories(connection)
    queued_workflow = _workflow("queued-workflow")
    active_workflow = _workflow("active-workflow")
    attention_workflow = _workflow("attention-workflow")
    run_ids: dict[str, tuple[str, str]] = {}
    for definition in (queued_workflow, active_workflow, attention_workflow):
        repository.save_workflow_definition(definition)
        run_id = repository.create_workflow_run(definition.id, definition.model_dump(mode="json"))
        task_run_id = repository.create_task_runs(run_id, ["A"])[0]
        repository.update_workflow_run_state(run_id, TaskStatus.RUNNING.value)
        run_ids[definition.id] = (run_id, task_run_id)
    repository.update_task_run_state(run_ids["active-workflow"][1], TaskStatus.RUNNING.value, "thread-active", "turn-active")
    repository.update_task_run_state(
        run_ids["attention-workflow"][1],
        TaskStatus.NEEDS_ATTENTION.value,
        "thread-attention",
        "turn-attention",
    )
    connection.close()

    restarted_connection = open_database(database_path)
    try:
        restarted_repository = StorageRepositories(restarted_connection)
        adapter = TrackingReadAdapter()
        reconciled = await StartupReconciler(restarted_connection, adapter).reconcile()

        assert set(reconciled) == {
            run_ids["active-workflow"][1],
            run_ids["attention-workflow"][1],
        }
        assert set(adapter.read_thread_ids) == {"thread-active", "thread-attention"}
        assert adapter.calls == ["read_thread", "read_thread"]
        assert restarted_repository.get_task_run(run_ids["queued-workflow"][1])["status"] == TaskStatus.PENDING.value
        assert restarted_repository.get_task_run(run_ids["active-workflow"][1])["status"] == TaskStatus.NEEDS_ATTENTION.value
        assert restarted_repository.get_task_run(run_ids["attention-workflow"][1])["status"] == TaskStatus.NEEDS_ATTENTION.value
        assert len({run_id for run_id, _ in run_ids.values()}) == 3
        assert len({task_id for _, task_id in run_ids.values()}) == 3
        for workflow_id, (_, task_run_id) in run_ids.items():
            event = restarted_connection.execute(
                "SELECT event_type FROM events WHERE task_run_id = ? ORDER BY rowid",
                (task_run_id,),
            ).fetchall()
            expected = [] if workflow_id == "queued-workflow" else ["RECOVERY_THREAD_REQUIRES_RECONCILIATION"]
            assert [row["event_type"] for row in event] == expected
    finally:
        restarted_connection.close()
