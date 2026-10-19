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
    def __init__(self, *, fail: bool = False) -> None:
        super().__init__()
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.fail = fail

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.started.set()
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        await self.release.wait()
        if self.fail:
            raise RuntimeError("stream failed")
        yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)


async def _start_manager(tmp_path: Path, adapter: BlockingAdapter) -> tuple[RuntimeManager, str, str]:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    manager = RuntimeManager(repository, adapter)
    run_id = await manager.start(workflow())
    task_run_id = str(repository.load_task_runs(run_id)[0]["id"])
    await adapter.started.wait()
    return manager, run_id, task_run_id


@pytest.mark.asyncio
async def test_active_turn_is_registered_only_while_turn_is_running(tmp_path: Path) -> None:
    adapter = BlockingAdapter()
    manager, run_id, task_run_id = await _start_manager(tmp_path, adapter)

    turn = manager.active_turn(task_run_id)
    assert turn is not None
    assert manager.active_turns == {task_run_id: turn}

    adapter.release.set()
    await manager.wait(run_id)
    assert manager.active_turn(task_run_id) is None
    assert manager.active_turns == {}


@pytest.mark.asyncio
async def test_active_turn_is_cleaned_when_stream_raises(tmp_path: Path) -> None:
    adapter = BlockingAdapter(fail=True)
    manager, run_id, task_run_id = await _start_manager(tmp_path, adapter)
    assert manager.active_turn(task_run_id) is not None

    adapter.release.set()
    with pytest.raises(RuntimeError, match="stream failed"):
        await manager.wait(run_id)
    assert manager.active_turn(task_run_id) is None
    assert manager.active_turns == {}
