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


class HangingAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.interrupt_count = 0

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        yield CodexEvent(
            event_type=EventType.TURN_STARTED,
            thread_id=turn.thread_id,
            turn_id=turn.turn_id,
        )
        await asyncio.Event().wait()

    async def interrupt_turn(self, turn: CodexTurnRef):  # type: ignore[no-untyped-def]
        self.interrupt_count += 1
        return await super().interrupt_turn(turn)


def workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="A", cwd=".", timeout_seconds=1),
            TaskDefinition(id="B", name="B", prompt="B", cwd=".", dependencies=["A"]),
        ],
        edges=[Edge(source_task_id="A", target_task_id="B")],
    )


@pytest.mark.asyncio
async def test_timeout_interrupts_once_and_blocks_child(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = HangingAdapter()
    manager = RuntimeManager(repository, adapter)

    run_id = await manager.start(workflow())
    await manager.wait(run_id)

    rows = {str(row["task_id"]): row for row in repository.load_task_runs(run_id)}
    assert rows["A"]["status"] == "INTERRUPTED"
    assert rows["B"]["status"] == "BLOCKED"
    assert adapter.interrupt_count == 1
    timeout_events = [
        event for event in repository.load_events_for_run(run_id) if event["event_type"] == "TASK_TIMEOUT"
    ]
    assert len(timeout_events) == 1
