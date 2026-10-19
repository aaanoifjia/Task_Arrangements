import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexTurnRef, EventType
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.runtime.manager import RuntimeManager
from codex_flow.runtime.runner import DurableRunner
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".")],
        edges=[],
    )


@pytest.mark.asyncio
async def test_cancel_before_external_thread_is_queued_and_does_not_call_adapter(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    manager = RuntimeManager(repository, FakeCodexAdapter())
    run_id = manager._runner.prepare_run(workflow())
    task_run_id = str(repository.load_task_runs(run_id)[0]["id"])

    result = await manager.cancel(run_id, task_run_id)

    assert result.accepted is True
    assert repository.get_task_run(task_run_id)["status"] == TaskStatus.CANCELLED  # type: ignore[index]


class StartTurnGateAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.start_turn_entered = asyncio.Event()
        self.release_start_turn = asyncio.Event()

    async def start_turn(self, thread, prompt):  # type: ignore[no-untyped-def]
        self.start_turn_entered.set()
        await self.release_start_turn.wait()
        return await super().start_turn(thread, prompt)


@pytest.mark.asyncio
async def test_cancel_after_thread_before_turn_fails_closed_without_duplicate_start(
    tmp_path: Path,
) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = StartTurnGateAdapter()
    manager = RuntimeManager(repository, adapter)
    run_id = await manager.start(workflow())
    await adapter.start_turn_entered.wait()
    task_run_id = str(repository.load_task_runs(run_id)[0]["id"])

    result = await manager.cancel(run_id, task_run_id)

    assert result.accepted is False
    assert result.error_code == "EXTERNAL_STATE_UNKNOWN"
    assert adapter.calls == ["create_thread"]
    adapter.release_start_turn.set()
    await manager.wait(run_id)
    assert adapter.calls.count("create_thread") == 1


class InterruptibleAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.started.set()
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        await self.release.wait()
        yield CodexEvent(event_type=EventType.TURN_INTERRUPTED, thread_id=turn.thread_id, turn_id=turn.turn_id)


@pytest.mark.asyncio
async def test_cancel_running_interrupts_once(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = InterruptibleAdapter()
    manager = RuntimeManager(repository, adapter)
    run_id = await manager.start(workflow())
    await adapter.started.wait()
    task_run_id = str(repository.load_task_runs(run_id)[0]["id"])

    first = await manager.cancel(run_id, task_run_id)
    second = await manager.cancel(run_id, task_run_id)
    adapter.release.set()
    await manager.wait(run_id)

    assert first.accepted is True
    assert second.accepted is False
    assert adapter.calls.count("interrupt_turn") == 1
    assert repository.get_task_run(task_run_id)["status"] == TaskStatus.CANCELLED  # type: ignore[index]


class TerminalRaceAdapter(FakeCodexAdapter):
    def __init__(self, repository: StorageRepositories, task_run_id: str | None = None) -> None:
        super().__init__()
        self.repository = repository
        self.task_run_id = task_run_id

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        if self.task_run_id is not None:
            self.repository.update_task_run_state(self.task_run_id, TaskStatus.CANCELLED.value)
        yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)


@pytest.mark.asyncio
async def test_cancel_just_before_terminal_persistence_wins(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = TerminalRaceAdapter(repository)
    runner = DurableRunner(repository, adapter)
    run_id = runner.prepare_run(workflow())
    task_run_id = str(repository.load_task_runs(run_id)[0]["id"])
    adapter.task_run_id = task_run_id

    await runner.execute_run(run_id, workflow())

    assert repository.get_task_run(task_run_id)["status"] == TaskStatus.CANCELLED  # type: ignore[index]
    assert len(repository.load_attempts(task_run_id)) == 1
