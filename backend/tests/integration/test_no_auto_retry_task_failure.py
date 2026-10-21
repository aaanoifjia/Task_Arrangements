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
                retry_policy=RetryPolicy(max_attempts=3),
            )
        ],
        edges=[],
    )


class FailureAdapter(FakeCodexAdapter):
    def __init__(self, outcome: str) -> None:
        super().__init__()
        self.outcome = outcome
        self.stream_count = 0

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.stream_count += 1
        yield CodexEvent(
            event_type=EventType.TURN_STARTED,
            thread_id=turn.thread_id,
            turn_id=turn.turn_id,
        )
        if self.outcome == "tool_failure":
            yield CodexEvent(
                event_type=EventType.TOOL_COMPLETED,
                thread_id=turn.thread_id,
                turn_id=turn.turn_id,
                details={"item_type": "command_execution", "status": "failed", "exit_code": 1},
            )
            yield CodexEvent(
                event_type=EventType.TURN_COMPLETED,
                thread_id=turn.thread_id,
                turn_id=turn.turn_id,
            )
        elif self.outcome == "task_failure":
            yield CodexEvent(
                event_type=EventType.TURN_FAILED,
                thread_id=turn.thread_id,
                turn_id=turn.turn_id,
            )
        elif self.outcome in {"permission", "validation"}:
            yield CodexEvent(
                event_type=EventType.ATTENTION_REQUIRED,
                thread_id=turn.thread_id,
                turn_id=turn.turn_id,
                details={"code": "PERMISSION_DENIED" if self.outcome == "permission" else "INVALID_PROMPT"},
            )
        elif self.outcome == "interrupt":
            yield CodexEvent(
                event_type=EventType.TURN_INTERRUPTED,
                thread_id=turn.thread_id,
                turn_id=turn.turn_id,
            )
        else:
            raise RuntimeError("unknown adapter failure")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("outcome", "expected_status"),
    [
        ("tool_failure", "FAILED"),
        ("task_failure", "FAILED"),
        ("permission", "NEEDS_ATTENTION"),
        ("validation", "NEEDS_ATTENTION"),
        ("interrupt", "INTERRUPTED"),
    ],
)
async def test_non_transient_outcomes_do_not_retry(
    tmp_path: Path, outcome: str, expected_status: str
) -> None:
    repository = StorageRepositories(open_database(tmp_path / f"{outcome}.sqlite3"))
    adapter = FailureAdapter(outcome)
    manager = RuntimeManager(repository, adapter)

    run_id = await manager.start(workflow())
    await manager.wait(run_id)

    task_run = repository.load_task_runs(run_id)[0]
    assert task_run["status"] == expected_status
    assert adapter.stream_count == 1
    assert len(repository.load_attempts(str(task_run["id"]))) == 1
    assert not any(
        str(event["event_type"]) == "RETRY_REQUESTED"
        for event in repository.load_events_for_run(run_id)
    )


@pytest.mark.asyncio
async def test_unknown_adapter_failure_does_not_retry(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "unknown.sqlite3"))
    adapter = FailureAdapter("unknown")
    manager = RuntimeManager(repository, adapter)

    run_id = await manager.start(workflow())
    with pytest.raises(RuntimeError, match="unknown adapter failure"):
        await manager.wait(run_id)

    task_run = repository.load_task_runs(run_id)[0]
    assert task_run["status"] == "RUNNING"
    assert adapter.stream_count == 1
    assert len(repository.load_attempts(str(task_run["id"]))) == 1
