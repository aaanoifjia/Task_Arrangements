"""Event cursor continuity across a storage and event-stream restart."""

from __future__ import annotations

from pathlib import Path

import pytest

from codex_flow.application.event_stream import EventStream
from codex_flow.application.events import EventApplicationService
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


@pytest.mark.asyncio
async def test_event_cursor_resumes_only_later_events_after_restart(tmp_path: Path) -> None:
    database_path = tmp_path / "cursor.sqlite3"
    connection = open_database(database_path)
    first_repository = StorageRepositories(connection)
    first_repository.save_workflow_definition(
        WorkflowDefinition(
            id="cursor-workflow",
            name="Cursor Workflow",
            tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".")],
            edges=[],
        )
    )
    run_id = first_repository.create_workflow_run("cursor-workflow", {})
    task_run_id = first_repository.create_task_runs(run_id, ["A"])[0]
    first_event_id = first_repository.append_event(
        "FIRST", {"sequence": 1}, workflow_run_id=run_id, task_run_id=task_run_id
    )
    second_event_id = first_repository.append_event(
        "SECOND", {"sequence": 2}, workflow_run_id=run_id, task_run_id=task_run_id
    )
    first_stream = EventStream(EventApplicationService(first_repository), poll_interval_seconds=0)
    events = first_stream.stream(run_id)
    try:
        first_message = await events.__anext__()
        second_message = await events.__anext__()
    finally:
        await events.aclose()
    connection.close()

    assert first_message.kind == "event"
    assert first_message.payload["id"] == first_event_id
    assert second_message.kind == "event"
    assert second_message.payload["id"] == second_event_id

    reopened_connection = open_database(database_path)
    try:
        reopened_repository = StorageRepositories(reopened_connection)
        third_event_id = reopened_repository.append_event(
            "THIRD", {"sequence": 3}, workflow_run_id=run_id, task_run_id=task_run_id
        )
        reopened_repository.update_workflow_run_state(run_id, "SUCCESS")
        resumed_stream = EventStream(
            EventApplicationService(reopened_repository), poll_interval_seconds=0
        )
        resumed_messages = [
            message async for message in resumed_stream.stream(run_id, after_event_id=second_event_id)
        ]
    finally:
        reopened_connection.close()

    resumed_events = [message for message in resumed_messages if message.kind == "event"]
    assert [message.payload["id"] for message in resumed_events] == [third_event_id]
    assert resumed_events[0].payload["event_type"] == "THIRD"
    assert resumed_messages[-1].kind == "snapshot"
