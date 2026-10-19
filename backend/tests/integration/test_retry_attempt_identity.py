from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexTurnRef, EventType
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.runtime.manager import RuntimeManager
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


class FailOnceAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.failed_once = False

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        terminal = EventType.TURN_FAILED if not self.failed_once else EventType.TURN_COMPLETED
        self.failed_once = True
        yield CodexEvent(event_type=terminal, thread_id=turn.thread_id, turn_id=turn.turn_id)


def workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".")],
        edges=[],
    )


@pytest.mark.asyncio
async def test_retry_attempts_have_distinct_immutable_external_identity(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    manager = RuntimeManager(repository, FailOnceAdapter())

    run_id = await manager.start(workflow())
    await manager.wait(run_id)
    task_run_id = str(repository.load_task_runs(run_id)[0]["id"])
    assert repository.load_task_runs(run_id)[0]["status"] == "FAILED"

    result = await manager.retry(run_id, task_run_id)
    assert result.accepted is True
    await manager.wait(run_id)

    attempts = repository.load_attempts(task_run_id)
    assert len(attempts) == 2
    assert attempts[0]["id"] != attempts[1]["id"]
    assert attempts[0]["status"] == "FAILED"
    assert attempts[1]["status"] == "SUCCESS"
    assert attempts[0]["thread_id"] is not None
    assert attempts[0]["turn_id"] is not None
    assert attempts[1]["thread_id"] is not None
    assert attempts[1]["turn_id"] is not None
    assert attempts[0]["thread_id"] != attempts[1]["thread_id"]
    assert attempts[0]["turn_id"] != attempts[1]["turn_id"]
