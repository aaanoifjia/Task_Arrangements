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


class MultiRunAdapter(FakeCodexAdapter):
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


def workflow(workflow_id: str, task_id: str) -> WorkflowDefinition:
    return WorkflowDefinition(
        id=workflow_id,
        name=workflow_id,
        tasks=[TaskDefinition(id=task_id, name=task_id, prompt=task_id, cwd=workflow_id)],
        edges=[],
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(("limit", "expected_peak"), [(1, 1), (2, 2)])
async def test_simultaneous_workflow_runs_share_global_capacity(
    tmp_path: Path, limit: int, expected_peak: int
) -> None:
    repository = StorageRepositories(open_database(tmp_path / f"flow-{limit}.sqlite3"))
    adapter = MultiRunAdapter()
    manager = RuntimeManager(repository, adapter, max_concurrency=limit)

    run_one, run_two = await asyncio.gather(
        manager.start(workflow("workflow-one", "A")),
        manager.start(workflow("workflow-two", "B")),
    )
    await asyncio.gather(manager.wait(run_one), manager.wait(run_two))

    assert adapter.peak == expected_peak
    assert repository.get_workflow_run(run_one)["status"] == "SUCCESS"
    assert repository.get_workflow_run(run_two)["status"] == "SUCCESS"
