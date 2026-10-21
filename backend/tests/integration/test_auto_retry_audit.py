import json
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexTurnRef, EventType
from codex_flow.domain.models import RetryPolicy, TaskDefinition, WorkflowDefinition
from codex_flow.runtime.manager import RuntimeManager
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def workflow(max_attempts: int) -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[
            TaskDefinition(
                id="A",
                name="A",
                prompt="A",
                cwd=".",
                retry_policy=RetryPolicy(max_attempts=max_attempts),
            )
        ],
        edges=[],
    )


class BusyAdapter(FakeCodexAdapter):
    def __init__(self, *, succeed_after_first: bool) -> None:
        super().__init__()
        self.succeed_after_first = succeed_after_first
        self.stream_count = 0

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.stream_count += 1
        yield CodexEvent(
            event_type=EventType.TURN_STARTED,
            thread_id=turn.thread_id,
            turn_id=turn.turn_id,
        )
        if self.succeed_after_first and self.stream_count > 1:
            yield CodexEvent(
                event_type=EventType.TURN_COMPLETED,
                thread_id=turn.thread_id,
                turn_id=turn.turn_id,
            )
            return
        yield CodexEvent(
            event_type=EventType.ATTENTION_REQUIRED,
            thread_id=turn.thread_id,
            turn_id=turn.turn_id,
            details={"code": "SERVER_BUSY", "secret": "must-not-be-audit-data"},
        )


async def _run(monkeypatch, tmp_path: Path, *, max_attempts: int, succeed_after_first: bool):
    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr("codex_flow.runtime.runner.sleep_backoff", no_sleep)
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = BusyAdapter(succeed_after_first=succeed_after_first)
    manager = RuntimeManager(repository, adapter)
    run_id = await manager.start(workflow(max_attempts))
    await manager.wait(run_id)
    return repository, adapter, run_id


@pytest.mark.asyncio
async def test_auto_retry_audit_order_and_payload(monkeypatch, tmp_path: Path) -> None:
    repository, adapter, run_id = await _run(
        monkeypatch, tmp_path, max_attempts=2, succeed_after_first=True
    )

    events = repository.load_events_for_run(run_id)
    audit = [event for event in events if event["event_type"] in {"AUTO_RETRY_SCHEDULED", "RETRY_REQUESTED"}]
    assert [event["event_type"] for event in audit] == ["AUTO_RETRY_SCHEDULED", "RETRY_REQUESTED"]
    payload = json.loads(str(audit[0]["payload_json"]))
    assert payload == {
        "attempt_number": 1,
        "max_attempts": 2,
        "next_attempt_number": 2,
        "reason_class": "SERVER_BUSY",
    }
    assert "secret" not in payload
    assert adapter.stream_count == 2


@pytest.mark.asyncio
async def test_auto_retry_exhausted_audit_is_last_retry_record(monkeypatch, tmp_path: Path) -> None:
    repository, _, run_id = await _run(
        monkeypatch, tmp_path, max_attempts=2, succeed_after_first=False
    )

    events = repository.load_events_for_run(run_id)
    audit = [
        event
        for event in events
        if event["event_type"] in {"AUTO_RETRY_SCHEDULED", "RETRY_REQUESTED", "AUTO_RETRY_EXHAUSTED"}
    ]
    assert [event["event_type"] for event in audit] == [
        "AUTO_RETRY_SCHEDULED",
        "RETRY_REQUESTED",
        "AUTO_RETRY_EXHAUSTED",
    ]
    payload = json.loads(str(audit[-1]["payload_json"]))
    assert payload == {"attempt_number": 2, "max_attempts": 2, "reason_class": "SERVER_BUSY"}
