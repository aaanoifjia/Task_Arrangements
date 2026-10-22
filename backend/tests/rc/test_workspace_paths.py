"""Release-candidate checks for durable workflows in space-containing paths."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexTurnRef, EventType
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.runtime.runner import DurableRunner
from codex_flow.scheduler.locks import canonical_workspace_key
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


class WorkspaceTrackingAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.active_streams = 0
        self.peak_streams = 0

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.calls.append("stream_turn")
        self.active_streams += 1
        self.peak_streams = max(self.peak_streams, self.active_streams)
        tracked = True
        try:
            yield CodexEvent(
                event_type=EventType.TURN_STARTED,
                thread_id=turn.thread_id,
                turn_id=turn.turn_id,
            )
            await asyncio.sleep(0)
            self.active_streams -= 1
            tracked = False
            yield CodexEvent(
                event_type=EventType.TURN_COMPLETED,
                thread_id=turn.thread_id,
                turn_id=turn.turn_id,
            )
        finally:
            if tracked:
                self.active_streams -= 1


@pytest.mark.asyncio
async def test_durable_workflow_preserves_spaced_workspace_and_serializes_writes(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "nested directory" / "workspace with multiple spaces"
    workspace.mkdir(parents=True)
    database_path = tmp_path / "app data" / "flow.sqlite3"
    database_path.parent.mkdir()
    workflow = WorkflowDefinition(
        id="spaced-path-workflow",
        name="Spaced Path Workflow",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="A", cwd=str(workspace)),
            TaskDefinition(id="B", name="B", prompt="B", cwd=str(workspace)),
        ],
        edges=[],
    )
    connection = open_database(database_path)
    try:
        repository = StorageRepositories(connection)
        adapter = WorkspaceTrackingAdapter()
        runner = DurableRunner(repository, adapter, max_concurrency=2)

        run_id = await runner.run(workflow)

        rows = repository.load_task_runs(run_id)
        run = repository.get_workflow_run(run_id)
        assert run is not None
        snapshot = json.loads(str(run["snapshot_json"]))
        snapshot_tasks = {task["id"]: task for task in snapshot["tasks"]}
        assert all(row["status"] == TaskStatus.SUCCESS.value for row in rows)
        assert all(snapshot_tasks[task_id]["cwd"] == str(workspace) for task_id in ("A", "B"))
        assert canonical_workspace_key(str(workspace)) == canonical_workspace_key(
            str(workspace / ".")
        )
        assert adapter.peak_streams == 1
        assert adapter.calls.count("create_thread") == 2
        assert adapter.calls.count("start_turn") == 2
        assert all(len(repository.load_attempts(str(row["id"]))) == 1 for row in rows)
    finally:
        connection.close()
