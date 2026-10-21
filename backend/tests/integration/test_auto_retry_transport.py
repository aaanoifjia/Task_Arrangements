from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexTurnRef, EventType
from codex_flow.domain.models import RetryPolicy, TaskDefinition, WorkflowDefinition
from codex_flow.runtime.manager import RuntimeManager
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


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


class SafeTransportAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.stream_count = 0

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.stream_count += 1
        if self.stream_count == 1:
            yield CodexEvent(
                event_type=EventType.TRANSPORT_ERROR,
                thread_id=turn.thread_id,
                turn_id=turn.turn_id,
                details={"code": "TRANSPORT_DISCONNECT"},
            )
            return
        yield CodexEvent(
            event_type=EventType.TURN_STARTED,
            thread_id=turn.thread_id,
            turn_id=turn.turn_id,
        )
        yield CodexEvent(
            event_type=EventType.TURN_COMPLETED,
            thread_id=turn.thread_id,
            turn_id=turn.turn_id,
        )


class AmbiguousTransportAdapter(FakeCodexAdapter):
    async def start_turn(self, thread, prompt: str):  # type: ignore[no-untyped-def]
        raise ConnectionError("transport reset during external start")


@pytest.mark.asyncio
async def test_safe_transport_retry_happens_before_turn_start(monkeypatch, tmp_path: Path) -> None:
    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr("codex_flow.runtime.runner.sleep_backoff", no_sleep)
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = SafeTransportAdapter()
    manager = RuntimeManager(repository, adapter)

    run_id = await manager.start(workflow())
    await manager.wait(run_id)

    task_run = repository.load_task_runs(run_id)[0]
    assert task_run["status"] == "SUCCESS"
    assert len(repository.load_attempts(str(task_run["id"]))) == 2
    assert adapter.stream_count == 2


@pytest.mark.asyncio
async def test_ambiguous_external_start_fails_closed_without_retry(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = AmbiguousTransportAdapter()
    manager = RuntimeManager(repository, adapter)

    run_id = await manager.start(workflow())
    with pytest.raises(ConnectionError):
        await manager.wait(run_id)

    task_run = repository.load_task_runs(run_id)[0]
    assert task_run["status"] == "STARTING"
    assert len(repository.load_attempts(str(task_run["id"]))) == 1
