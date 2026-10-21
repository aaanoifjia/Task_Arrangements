import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexTurnRef, EventType
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.runtime.runner import DurableRunner
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


class TrackingAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.active = 0
        self.peak = 0

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.calls.append("stream_turn")
        self.active += 1
        self.peak = max(self.peak, self.active)
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        await asyncio.sleep(0.05)
        self.active -= 1
        yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)


def workflow(cwd: str) -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="A", cwd=cwd),
            TaskDefinition(id="B", name="B", prompt="B", cwd=cwd),
        ],
        edges=[],
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(("cwd", "expected_peak"), [("same", 1), ("different-a", 2)])
async def test_durable_workspace_write_lock_serializes_same_cwd_only(
    tmp_path: Path, cwd: str, expected_peak: int
) -> None:
    definition = workflow(cwd)
    if cwd == "different-a":
        definition = definition.model_copy(
            update={
                "tasks": [
                    TaskDefinition(id="A", name="A", prompt="A", cwd="workspace-a"),
                    TaskDefinition(id="B", name="B", prompt="B", cwd="workspace-b"),
                ]
            }
        )
    repository = StorageRepositories(open_database(tmp_path / f"{cwd}.sqlite3"))
    adapter = TrackingAdapter()
    runner = DurableRunner(repository, adapter, max_concurrency=2)
    run_id = runner.prepare_run(definition)

    await runner.execute_run(run_id, definition)

    assert adapter.peak == expected_peak
    assert {row["status"] for row in repository.load_task_runs(run_id)} == {"SUCCESS"}
