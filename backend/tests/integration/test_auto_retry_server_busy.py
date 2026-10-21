from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexTurnRef, EventType
from codex_flow.domain.models import RetryPolicy, TaskDefinition, WorkflowDefinition
from codex_flow.runtime.manager import RuntimeManager
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


class BusyThenSuccessAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.stream_count = 0

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.stream_count += 1
        yield CodexEvent(
            event_type=EventType.TURN_STARTED,
            thread_id=turn.thread_id,
            turn_id=turn.turn_id,
        )
        if self.stream_count == 1:
            yield CodexEvent(
                event_type=EventType.ATTENTION_REQUIRED,
                thread_id=turn.thread_id,
                turn_id=turn.turn_id,
                details={"code": "SERVER_BUSY"},
            )
            return
        yield CodexEvent(
            event_type=EventType.TURN_COMPLETED,
            thread_id=turn.thread_id,
            turn_id=turn.turn_id,
        )


def workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[
            TaskDefinition(
                id="A",
                name="A",
                prompt="A",
                cwd=".",
                retry_policy=RetryPolicy(max_attempts=2),
            )
        ],
        edges=[],
    )


@pytest.mark.asyncio
async def test_server_busy_retry_creates_distinct_attempts_and_succeeds(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = BusyThenSuccessAdapter()
    manager = RuntimeManager(repository, adapter)

    run_id = await manager.start(workflow())
    await manager.wait(run_id)

    task_run = repository.load_task_runs(run_id)[0]
    attempts = repository.load_attempts(str(task_run["id"]))
    events = repository.load_events_for_run(run_id)
    assert task_run["status"] == "SUCCESS"
    assert len(attempts) == 2
    assert [str(attempt["status"]) for attempt in attempts] == ["NEEDS_ATTENTION", "SUCCESS"]
    assert any(str(event["event_type"]) == "RETRY_REQUESTED" for event in events)
    assert adapter.stream_count == 2
