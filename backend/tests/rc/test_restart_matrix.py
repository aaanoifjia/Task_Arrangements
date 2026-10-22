"""Queued-run restart checks for the offline release-candidate matrix."""

from __future__ import annotations

from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexThreadRef, CodexTurnRef
from codex_flow.domain.models import Edge, TaskDefinition, WorkflowDefinition
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
