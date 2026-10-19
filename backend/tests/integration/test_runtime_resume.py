import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexTurnRef, EventType
from codex_flow.domain.models import Edge, TaskDefinition, WorkflowDefinition
from codex_flow.runtime.manager import RuntimeManager
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="A", cwd="."),
            TaskDefinition(id="B", name="B", prompt="B", cwd=".", dependencies=["A"]),
        ],
        edges=[Edge(source_task_id="A", target_task_id="B")],
    )


class PauseOnceAdapter(FakeCodexAdapter):
    def __init__(self, repository: StorageRepositories) -> None:
        super().__init__()
        self.repository = repository
        self.run_id: str | None = None
        self.paused = False

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        async for event in super().stream_turn(turn):
            yield event
            if event.event_type is EventType.TURN_STARTED and self.run_id and not self.paused:
                self.paused = True
                self.repository.set_workflow_run_paused(self.run_id, True)


class BlockingAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.started.set()
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        await self.release.wait()
        yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)


@pytest.mark.asyncio
async def test_resume_reenters_paused_run_and_continues_ready_work(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = PauseOnceAdapter(repository)
    manager = RuntimeManager(repository, adapter)
    run_id = await manager.start(workflow())
    adapter.run_id = run_id
    await manager.wait(run_id)

    paused_rows = {row["task_id"]: row["status"] for row in repository.load_task_runs(run_id)}
    assert paused_rows == {"A": "SUCCESS", "B": "BLOCKED"}
    assert repository.get_workflow_run_paused(run_id) is True

    result = await manager.resume(run_id)
    assert result.accepted is True
    assert repository.get_workflow_run_paused(run_id) is False
    await manager.wait(run_id)
    assert {row["task_id"]: row["status"] for row in repository.load_task_runs(run_id)} == {
        "A": "SUCCESS",
        "B": "SUCCESS",
    }
    assert adapter.calls == ["create_thread", "start_turn", "stream_turn"] * 2


@pytest.mark.asyncio
async def test_resume_does_not_create_duplicate_runner_for_active_turn(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = BlockingAdapter()
    manager = RuntimeManager(repository, adapter)
    run_id = await manager.start(workflow())
    await adapter.started.wait()
    await manager.pause(run_id)

    result = await manager.resume(run_id)
    assert result.accepted is True
    assert manager.active_count == 1
    assert adapter.calls.count("create_thread") == 1

    adapter.release.set()
    await manager.wait(run_id)
    assert repository.get_workflow_run_paused(run_id) is False


@pytest.mark.asyncio
async def test_duplicate_resume_of_unpaused_or_terminal_run_is_rejected(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    manager = RuntimeManager(repository, FakeCodexAdapter())
    run_id = await manager.start(workflow().model_copy(update={"tasks": [workflow().tasks[0]], "edges": []}))
    await manager.wait(run_id)

    result = await manager.resume(run_id)
    assert result.accepted is False
    assert result.error_code == "RUN_NOT_ACTIVE"
