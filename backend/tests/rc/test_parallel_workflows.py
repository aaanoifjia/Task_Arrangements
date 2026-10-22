"""Event-synchronized independent workspace parallelism checks."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexTurnRef, EventType
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.runtime.runner import DurableRunner
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


class OverlapAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.active_streams = 0
        self.peak_streams = 0
        self.two_started = asyncio.Event()
        self.release = asyncio.Event()

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.calls.append("stream_turn")
        self.active_streams += 1
        self.peak_streams = max(self.peak_streams, self.active_streams)
        tracked = True
        try:
            yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
            if self.active_streams == 2:
                self.two_started.set()
            await self.release.wait()
            self.active_streams -= 1
            tracked = False
            yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        finally:
            if tracked:
                self.active_streams -= 1


class SerializationAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.active_streams = 0
        self.peak_streams = 0
        self.started_count = 0
        self.first_started = asyncio.Event()
        self.second_started = asyncio.Event()
        self.release = asyncio.Event()

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.calls.append("stream_turn")
        self.active_streams += 1
        self.peak_streams = max(self.peak_streams, self.active_streams)
        self.started_count += 1
        if self.started_count == 1:
            self.first_started.set()
        if self.started_count == 2:
            self.second_started.set()
        tracked = True
        try:
            yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
            await self.release.wait()
            self.active_streams -= 1
            tracked = False
            yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        finally:
            if tracked:
                self.active_streams -= 1


@pytest.mark.asyncio
async def test_independent_workspace_tasks_overlap_at_configured_capacity(tmp_path: Path) -> None:
    workspace_a = tmp_path / "workspace-a"
    workspace_b = tmp_path / "workspace-b"
    workspace_a.mkdir()
    workspace_b.mkdir()
    workflow = WorkflowDefinition(
        id="parallel-workspace-workflow",
        name="Parallel Workspace Workflow",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="A", cwd=str(workspace_a)),
            TaskDefinition(id="B", name="B", prompt="B", cwd=str(workspace_b)),
        ],
        edges=[],
    )
    connection = open_database(tmp_path / "parallel.sqlite3")
    try:
        repository = StorageRepositories(connection)
        adapter = OverlapAdapter()
        runner = DurableRunner(repository, adapter, max_concurrency=2)
        run_task = asyncio.create_task(runner.run(workflow))
        await adapter.two_started.wait()
        assert adapter.active_streams == 2
        adapter.release.set()
        run_id = await run_task

        rows = repository.load_task_runs(run_id)
        assert adapter.peak_streams == 2
        assert [row["status"] for row in rows] == [TaskStatus.SUCCESS.value, TaskStatus.SUCCESS.value]
        assert all(len(repository.load_attempts(str(row["id"]))) == 1 for row in rows)
    finally:
        connection.close()


@pytest.mark.asyncio
async def test_equivalent_same_workspace_paths_never_overlap(tmp_path: Path) -> None:
    workspace = tmp_path / "shared workspace"
    workspace.mkdir()
    workflow = WorkflowDefinition(
        id="serialized-workspace-workflow",
        name="Serialized Workspace Workflow",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="A", cwd=str(workspace)),
            TaskDefinition(id="B", name="B", prompt="B", cwd=str(workspace / ".")),
        ],
        edges=[],
    )
    connection = open_database(tmp_path / "serialized.sqlite3")
    try:
        repository = StorageRepositories(connection)
        adapter = SerializationAdapter()
        runner = DurableRunner(repository, adapter, max_concurrency=2)
        run_task = asyncio.create_task(runner.run(workflow))
        await adapter.first_started.wait()
        assert adapter.active_streams == 1
        assert not adapter.second_started.is_set()
        adapter.release.set()
        run_id = await run_task

        rows = repository.load_task_runs(run_id)
        assert adapter.peak_streams == 1
        assert adapter.second_started.is_set()
        assert [row["status"] for row in rows] == [TaskStatus.SUCCESS.value, TaskStatus.SUCCESS.value]
    finally:
        connection.close()
