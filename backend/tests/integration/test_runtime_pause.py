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
        tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".")],
        edges=[],
    )


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
async def test_pause_is_durable_and_does_not_interrupt_active_turn(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = BlockingAdapter()
    manager = RuntimeManager(repository, adapter)
    run_id = await manager.start(workflow())
    await adapter.started.wait()
    task_run_id = str(repository.load_task_runs(run_id)[0]["id"])
    active_turn = manager.active_turn(task_run_id)

    result = await manager.pause(run_id)

    assert result.accepted is True
    assert repository.get_workflow_run_paused(run_id) is True
    assert manager.active_turn(task_run_id) == active_turn
    assert "interrupt_turn" not in adapter.calls
    audit = repository.load_events_for_run(run_id)[-1]
    assert audit["event_type"] == "MANUAL_ACTION_ACCEPTED"

    adapter.release.set()
    await manager.wait(run_id)
    assert repository.get_workflow_run(run_id)["status"] == "SUCCESS"  # type: ignore[index]
    assert repository.get_workflow_run_paused(run_id) is True


@pytest.mark.asyncio
async def test_pause_rejects_terminal_run_and_audits_rejection(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    manager = RuntimeManager(repository, FakeCodexAdapter())
    run_id = await manager.start(workflow())
    await manager.wait(run_id)

    result = await manager.pause(run_id)

    assert result.accepted is False
    assert result.error_code == "RUN_NOT_ACTIVE"
    assert repository.get_workflow_run_paused(run_id) is False
    assert repository.load_events_for_run(run_id)[-1]["event_type"] == "MANUAL_ACTION_REJECTED"
