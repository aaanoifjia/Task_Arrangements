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


class FailParentOnceAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.failed_once = False

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        terminal = EventType.TURN_FAILED if not self.failed_once else EventType.TURN_COMPLETED
        self.failed_once = True
        yield CodexEvent(event_type=terminal, thread_id=turn.thread_id, turn_id=turn.turn_id)


@pytest.mark.asyncio
async def test_retry_success_releases_blocked_child_once(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = FailParentOnceAdapter()
    manager = RuntimeManager(repository, adapter)

    run_id = await manager.start(workflow())
    await manager.wait(run_id)
    rows = {row["task_id"]: row for row in repository.load_task_runs(run_id)}
    parent_id = str(rows["A"]["id"])
    child_id = str(rows["B"]["id"])
    assert rows["A"]["status"] == "FAILED"
    assert rows["B"]["status"] == "BLOCKED"

    result = await manager.retry(run_id, parent_id)
    assert result.accepted is True
    await manager.wait(run_id)

    assert {row["task_id"]: row["status"] for row in repository.load_task_runs(run_id)} == {
        "A": "SUCCESS",
        "B": "SUCCESS",
    }
    assert len(repository.load_attempts(child_id)) == 1
    assert adapter.calls.count("start_turn") == 3
