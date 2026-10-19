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
async def test_cancel_running_interrupts_once_and_cancel_wins_late_terminal(
    tmp_path: Path,
) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = InterruptibleAdapter()
    manager = RuntimeManager(repository, adapter)
    run_id = await manager.start(workflow())
    await adapter.started.wait()
    task_run_id = str(repository.load_task_runs(run_id)[0]["id"])

    result = await manager.cancel(run_id, task_run_id)
    duplicate = await manager.cancel(run_id, task_run_id)

    assert result.accepted is True
    assert duplicate.accepted is False
    assert duplicate.error_code == "TASK_NOT_QUEUED"
    assert adapter.calls.count("interrupt_turn") == 1
    task_run = repository.get_task_run(task_run_id)
    assert task_run is not None and task_run["status"] == "CANCELLED"
    assert repository.load_attempts(task_run_id)[0]["status"] == "CANCELLED"

    adapter.release.set()
    await manager.wait(run_id)
    assert repository.get_task_run(task_run_id)["status"] == "CANCELLED"  # type: ignore[index]


@pytest.mark.asyncio
async def test_cancel_running_without_registry_turn_fails_closed(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    manager = RuntimeManager(repository, FakeCodexAdapter())
    repository.save_workflow_definition(workflow())
    run_id = repository.create_workflow_run("workflow", {"workflow": "snapshot"})
    task_run_id = repository.create_task_runs(run_id, ["A"])[0]
    repository.update_task_run_state(task_run_id, "RUNNING", "thread", "turn")

    result = await manager.cancel(run_id, task_run_id)

    assert result.accepted is False
    assert result.error_code == "EXTERNAL_STATE_UNKNOWN"
    assert repository.get_task_run(task_run_id)["status"] == "RUNNING"  # type: ignore[index]
