import asyncio
from collections.abc import AsyncIterator
from contextlib import suppress
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexTurnRef, EventType
from codex_flow.domain.models import Edge, ExecutionMode, TaskDefinition, WorkflowDefinition
from codex_flow.runtime.manager import RuntimeManager
from codex_flow.runtime.runner import DurableRunner
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def linear_workflow(*, continuation: bool = False) -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="A", cwd="."),
            TaskDefinition(
                id="B",
                name="B",
                prompt="B",
                cwd=".",
                dependencies=["A"],
                execution_mode=(ExecutionMode.CONTINUE_THREAD if continuation else ExecutionMode.NEW_THREAD),
                continue_from_task_id=("A" if continuation else None),
            ),
        ],
        edges=[Edge(source_task_id="A", target_task_id="B")],
    )


def independent_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="A", cwd="workspace-a"),
            TaskDefinition(id="B", name="B", prompt="B", cwd="workspace-b"),
        ],
        edges=[],
    )


class TrackingAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.active_streams = 0
        self.peak_streams = 0

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.calls.append("stream_turn")
        self.active_streams += 1
        self.peak_streams = max(self.peak_streams, self.active_streams)
        try:
            yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
            await asyncio.sleep(0)
            self.active_streams -= 1
            yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        finally:
            self.active_streams = max(self.active_streams, 0)


class HangingAdapter(FakeCodexAdapter):
    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.calls.append("stream_turn")
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        await asyncio.Event().wait()


class FailedCommandAdapter(FakeCodexAdapter):
    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.calls.append("stream_turn")
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        yield CodexEvent(
            event_type=EventType.TOOL_COMPLETED,
            thread_id=turn.thread_id,
            turn_id=turn.turn_id,
            details={"item_type": "command_execution", "status": "failed", "exit_code": 1},
        )
        yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)


@pytest.mark.asyncio
async def test_durable_runner_continuation_parity_gap(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = FakeCodexAdapter()
    manager = RuntimeManager(repository, adapter)

    run_id = await manager.start(linear_workflow(continuation=True))
    await manager.wait(run_id)

    assert adapter.calls.count("create_thread") == 1
    assert adapter.calls.count("resume_thread") == 1


@pytest.mark.asyncio
@pytest.mark.xfail(strict=True, reason="M10-HARDEN-005/006 add configured parallel durable execution")
async def test_durable_runner_parallelism_parity_gap(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = TrackingAdapter()
    runner = DurableRunner(repository, adapter)
    workflow = independent_workflow()
    run_id = runner.prepare_run(workflow)

    await runner.execute_run(run_id, workflow)

    assert adapter.peak_streams == 2


@pytest.mark.asyncio
async def test_durable_runner_preserves_same_workspace_write_serialization(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = TrackingAdapter()
    runner = DurableRunner(repository, adapter)
    workflow = independent_workflow().model_copy(
        update={"tasks": [
            TaskDefinition(id="A", name="A", prompt="A", cwd="same"),
            TaskDefinition(id="B", name="B", prompt="B", cwd="same"),
        ]}
    )
    run_id = runner.prepare_run(workflow)

    await runner.execute_run(run_id, workflow)

    assert adapter.peak_streams == 1


@pytest.mark.asyncio
async def test_durable_runner_retry_and_failure_propagation_match_scheduler(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    manager = RuntimeManager(repository, FailedCommandAdapter())
    run_id = await manager.start(linear_workflow())
    await manager.wait(run_id)

    rows = {row["task_id"]: row for row in repository.load_task_runs(run_id)}
    assert rows["A"]["status"] == "FAILED"
    assert rows["B"]["status"] == "BLOCKED"


@pytest.mark.asyncio
@pytest.mark.xfail(strict=True, reason="M10-HARDEN-019 adds durable task timeout enforcement")
async def test_durable_runner_timeout_parity_gap(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = HangingAdapter()
    workflow = WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".", timeout_seconds=1)],
        edges=[],
    )
    runner = DurableRunner(repository, adapter)
    run_id = runner.prepare_run(workflow)
    task = asyncio.create_task(runner.execute_run(run_id, workflow))
    try:
        await asyncio.sleep(0.05)
        row = repository.load_task_runs(run_id)[0]
        assert row["status"] == "FAILED"
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
