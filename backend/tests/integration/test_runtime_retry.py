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


class FailOnceAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.failed_once = False

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        terminal = EventType.TURN_FAILED if not self.failed_once else EventType.TURN_COMPLETED
        self.failed_once = True
        yield CodexEvent(event_type=terminal, thread_id=turn.thread_id, turn_id=turn.turn_id)


@pytest.mark.asyncio
async def test_retry_reopens_run_and_creates_fresh_attempt_without_overwrite(
    tmp_path: Path,
) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    manager = RuntimeManager(repository, FailOnceAdapter())
    run_id = await manager.start(workflow())
    await manager.wait(run_id)

    rows = {row["task_id"]: row for row in repository.load_task_runs(run_id)}
    parent_id = str(rows["A"]["id"])
    assert rows["A"]["status"] == "FAILED"
    assert rows["B"]["status"] == "BLOCKED"
    old_attempts = repository.load_attempts(parent_id)
    assert len(old_attempts) == 1
    old_attempt_id = old_attempts[0]["id"]

    result = await manager.retry(run_id, parent_id)

    assert result.accepted is True
    assert result.retry_requested is True
    assert result.status is None
    assert len(repository.load_attempts(parent_id)) == 1
    await manager.wait(run_id)

    assert {row["task_id"]: row["status"] for row in repository.load_task_runs(run_id)} == {
        "A": "SUCCESS",
        "B": "SUCCESS",
    }
    attempts = repository.load_attempts(parent_id)
    assert len(attempts) == 2
    assert attempts[0]["id"] == old_attempt_id
    assert attempts[1]["id"] != old_attempt_id
    assert repository.load_events_for_run(run_id)[-1]["event_type"] == "MANUAL_ACTION_ACCEPTED"
