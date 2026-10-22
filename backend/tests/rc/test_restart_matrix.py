"""Queued-run restart checks for the offline release-candidate matrix."""

from __future__ import annotations

from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexThreadRef, CodexTurnRef
from codex_flow.domain.models import Edge, TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.runtime.manager import RuntimeManager
from codex_flow.runtime.runner import DurableRunner
from codex_flow.storage.db import open_database
from codex_flow.storage.recovery import StartupReconciler
from codex_flow.storage.repositories import StorageRepositories


class RecordingAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.prompts: list[str] = []

    async def start_turn(self, thread: CodexThreadRef, prompt: str) -> CodexTurnRef:
        self.prompts.append(prompt)
        return await super().start_turn(thread, prompt)


@pytest.mark.asyncio
async def test_queued_run_restart_is_fail_closed_and_executes_once(tmp_path: Path) -> None:
    database_path = tmp_path / "queued-restart.sqlite3"
    workflow = WorkflowDefinition(
        id="queued-restart-workflow",
        name="Queued Restart Workflow",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="parent", cwd="."),
            TaskDefinition(id="B", name="B", prompt="child", cwd=".", dependencies=["A"]),
        ],
        edges=[Edge(source_task_id="A", target_task_id="B")],
    )
    first_connection = open_database(database_path)
    first_repository = StorageRepositories(first_connection)
    first_runner = DurableRunner(first_repository, RecordingAdapter())
    run_id = first_runner.prepare_run(workflow)
    assert [row["status"] for row in first_repository.load_task_runs(run_id)] == ["PENDING", "PENDING"]
    first_connection.close()

    restarted_connection = open_database(database_path)
    try:
        restarted_repository = StorageRepositories(restarted_connection)
        restarted_adapter = RecordingAdapter()
        assert await StartupReconciler(restarted_connection, restarted_adapter).reconcile() == []
        assert restarted_adapter.calls == []
        assert [row["status"] for row in restarted_repository.load_task_runs(run_id)] == [
            "PENDING",
            "PENDING",
        ]

        await DurableRunner(restarted_repository, restarted_adapter).execute_run(run_id, workflow)

        rows = restarted_repository.load_task_runs(run_id)
        assert [row["status"] for row in rows] == ["SUCCESS", "SUCCESS"]
        assert restarted_adapter.prompts == ["parent", "child"]
        assert restarted_adapter.calls.count("create_thread") == 2
        assert restarted_adapter.calls.count("start_turn") == 2
        assert restarted_repository.get_workflow_run(run_id)["status"] == "SUCCESS"
    finally:
        restarted_connection.close()


@pytest.mark.asyncio
async def test_paused_run_restart_releases_work_only_after_explicit_resume(tmp_path: Path) -> None:
    database_path = tmp_path / "paused-restart.sqlite3"
    workflow = WorkflowDefinition(
        id="paused-restart-workflow",
        name="Paused Restart Workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="paused", cwd=".")],
        edges=[],
    )
    connection = open_database(database_path)
    repository = StorageRepositories(connection)
    repository.save_workflow_definition(workflow)
    run_id = repository.create_workflow_run(workflow.id, workflow.model_dump(mode="json"))
    task_run_id = repository.create_task_runs(run_id, ["A"])[0]
    repository.update_workflow_run_state(run_id, TaskStatus.RUNNING.value)
    repository.set_workflow_run_paused(run_id, True)
    connection.close()

    restarted_connection = open_database(database_path)
    try:
        restarted_repository = StorageRepositories(restarted_connection)
        adapter = RecordingAdapter()
        assert await StartupReconciler(restarted_connection, adapter).reconcile() == []
        assert adapter.calls == []
        assert restarted_repository.get_workflow_run_paused(run_id)

        manager = RuntimeManager(restarted_repository, adapter)
        manager.restore_workflow(run_id, workflow)
        result = await manager.resume(run_id)
        await manager.wait(run_id)

        assert result.accepted
        assert adapter.prompts == ["paused"]
        assert restarted_repository.get_workflow_run_paused(run_id) is False
        assert restarted_repository.get_task_run(task_run_id)["status"] == TaskStatus.SUCCESS.value
    finally:
        restarted_connection.close()


@pytest.mark.asyncio
async def test_paused_active_run_reconciles_without_new_thread_start(tmp_path: Path) -> None:
    database_path = tmp_path / "paused-active-restart.sqlite3"
    workflow = WorkflowDefinition(
        id="paused-active-workflow",
        name="Paused Active Workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="active", cwd=".")],
        edges=[],
    )
    connection = open_database(database_path)
    repository = StorageRepositories(connection)
    repository.save_workflow_definition(workflow)
    run_id = repository.create_workflow_run(workflow.id, workflow.model_dump(mode="json"))
    task_run_id = repository.create_task_runs(run_id, ["A"])[0]
    repository.update_workflow_run_state(run_id, TaskStatus.RUNNING.value)
    repository.set_workflow_run_paused(run_id, True)
    repository.update_task_run_state(task_run_id, TaskStatus.RUNNING.value, "existing-thread", "existing-turn")
    connection.close()

    restarted_connection = open_database(database_path)
    try:
        restarted_repository = StorageRepositories(restarted_connection)
        adapter = RecordingAdapter()
        assert await StartupReconciler(restarted_connection, adapter).reconcile() == [task_run_id]
        assert adapter.calls == ["read_thread"]
        assert restarted_repository.get_workflow_run_paused(run_id)
        assert restarted_repository.get_task_run(task_run_id)["status"] == TaskStatus.NEEDS_ATTENTION.value
        assert "create_thread" not in adapter.calls
    finally:
        restarted_connection.close()


@pytest.mark.asyncio
async def test_needs_attention_restart_remains_actionable_without_rerun(tmp_path: Path) -> None:
    database_path = tmp_path / "attention-restart.sqlite3"
    workflow = WorkflowDefinition(
        id="attention-restart-workflow",
        name="Attention Restart Workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="attention", cwd=".")],
        edges=[],
    )
    connection = open_database(database_path)
    repository = StorageRepositories(connection)
    repository.save_workflow_definition(workflow)
    run_id = repository.create_workflow_run(workflow.id, workflow.model_dump(mode="json"))
    task_run_id = repository.create_task_runs(run_id, ["A"])[0]
    repository.update_workflow_run_state(run_id, TaskStatus.RUNNING.value)
    repository.update_task_run_state(
        task_run_id, TaskStatus.NEEDS_ATTENTION.value, "attention-thread", "attention-turn"
    )
    connection.close()

    restarted_connection = open_database(database_path)
    try:
        restarted_repository = StorageRepositories(restarted_connection)
        adapter = RecordingAdapter()
        reconciled = await StartupReconciler(restarted_connection, adapter).reconcile()

        assert reconciled == [task_run_id]
        assert adapter.calls == ["read_thread"]
        assert adapter.prompts == []
        assert restarted_repository.get_task_run(task_run_id)["status"] == TaskStatus.NEEDS_ATTENTION.value
        recovery_events = restarted_connection.execute(
            "SELECT event_type FROM events WHERE task_run_id = ? ORDER BY rowid",
            (task_run_id,),
        ).fetchall()
        assert [event["event_type"] for event in recovery_events] == [
            "RECOVERY_THREAD_REQUIRES_RECONCILIATION"
        ]
    finally:
        restarted_connection.close()
