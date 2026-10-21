import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexTurnRef, EventType
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.runtime.manager import RuntimeManager
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".", timeout_seconds=1)],
        edges=[],
    )


class ImmediateTerminalAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.interrupt_count = 0

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)

    async def interrupt_turn(self, turn: CodexTurnRef):  # type: ignore[no-untyped-def]
        self.interrupt_count += 1
        return await super().interrupt_turn(turn)


class LateTerminalAdapter(ImmediateTerminalAdapter):
    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        await asyncio.Event().wait()
        yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)


@pytest.mark.asyncio
async def test_terminal_before_timeout_is_canonical(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "immediate.sqlite3"))
    adapter = ImmediateTerminalAdapter()
    manager = RuntimeManager(repository, adapter)

    run_id = await manager.start(workflow())
    await manager.wait(run_id)

    task_run = repository.load_task_runs(run_id)[0]
    assert task_run["status"] == "SUCCESS"
    assert adapter.interrupt_count == 0
    assert not any(event["event_type"] == "TASK_TIMEOUT" for event in repository.load_events_for_run(run_id))


@pytest.mark.asyncio
async def test_timeout_wins_and_late_terminal_cannot_overwrite(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "late.sqlite3"))
    adapter = LateTerminalAdapter()
    manager = RuntimeManager(repository, adapter)

    run_id = await manager.start(workflow())
    await manager.wait(run_id)

    task_run = repository.load_task_runs(run_id)[0]
    assert task_run["status"] == "INTERRUPTED"
    assert adapter.interrupt_count == 1
    assert manager._runner._update_execution_state(
        str(task_run["id"]), "SUCCESS", "late-thread", "late-turn"
    ) is False
    assert repository.load_task_runs(run_id)[0]["status"] == "INTERRUPTED"
