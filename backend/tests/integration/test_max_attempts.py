from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexTurnRef, EventType
from codex_flow.domain.models import Edge, RetryPolicy, TaskDefinition, WorkflowDefinition
from codex_flow.runtime.manager import RuntimeManager
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


class AlwaysBusyAdapter(FakeCodexAdapter):
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
        yield CodexEvent(
            event_type=EventType.ATTENTION_REQUIRED,
            thread_id=turn.thread_id,
            turn_id=turn.turn_id,
            details={"code": "SERVER_BUSY"},
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
                retry_policy=RetryPolicy(max_attempts=3),
            ),
            TaskDefinition(id="B", name="B", prompt="B", cwd=".", dependencies=["A"]),
        ],
        edges=[Edge(source_task_id="A", target_task_id="B")],
    )


@pytest.mark.asyncio
async def test_max_attempts_stops_transient_retry_and_blocks_child(
    monkeypatch, tmp_path: Path
) -> None:
    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr("codex_flow.runtime.runner.sleep_backoff", no_sleep)
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = AlwaysBusyAdapter()
    manager = RuntimeManager(repository, adapter)

    run_id = await manager.start(workflow())
    await manager.wait(run_id)

    rows = {str(row["task_id"]): row for row in repository.load_task_runs(run_id)}
    attempts = repository.load_attempts(str(rows["A"]["id"]))
    assert rows["A"]["status"] == "NEEDS_ATTENTION"
    assert rows["B"]["status"] == "BLOCKED"
    assert len(attempts) == 3
    assert adapter.stream_count == 3
    assert len([event for event in repository.load_events_for_run(run_id) if event["event_type"] == "RETRY_REQUESTED"]) == 2
