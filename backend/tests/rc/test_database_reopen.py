"""SQLite reopen matrix for the release-candidate durable state contract."""

from __future__ import annotations

import json
from pathlib import Path

from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def test_database_reopen_preserves_run_snapshot_attempt_controls_and_events(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "app data" / "reopen.sqlite3"
    database_path.parent.mkdir()
    workflow = WorkflowDefinition(
        id="reopen-workflow",
        name="Reopen Workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="persist", cwd=".")],
        edges=[],
    )
    connection = open_database(database_path)
    first = StorageRepositories(connection)
    first.save_workflow_definition(workflow)
    run_id = first.create_workflow_run(workflow.id, workflow.model_dump(mode="json"))
    task_run_id = first.create_task_runs(run_id, ["A"])[0]
    attempt_id = first.create_attempt(task_run_id)
    first.update_workflow_run_state(run_id, "RUNNING")
    first.update_task_run_state(task_run_id, "RUNNING", "thread-reopen", "turn-reopen")
    first.update_attempt_state(attempt_id, "RUNNING")
    connection.execute(
        "UPDATE attempts SET thread_id = ?, turn_id = ? WHERE id = ?",
        ("thread-reopen", "turn-reopen", attempt_id),
    )
    connection.commit()
    first.set_workflow_run_paused(run_id, True)
    first.append_event(
        "FIRST",
        {"sequence": 1},
        workflow_run_id=run_id,
        task_run_id=task_run_id,
        attempt_id=attempt_id,
    )
    second_event_id = first.append_event(
        "SECOND",
        {"sequence": 2},
        workflow_run_id=run_id,
        task_run_id=task_run_id,
        attempt_id=attempt_id,
    )
    first_snapshot = json.loads(str(first.get_workflow_run(run_id)["snapshot_json"]))
    connection.close()

    reopened_connection = open_database(database_path)
    try:
        reopened = StorageRepositories(reopened_connection)
        reopened_run = reopened.get_workflow_run(run_id)
        reopened_task = reopened.get_task_run(task_run_id)
        reopened_attempt = reopened.load_attempts(task_run_id)[0]
        events = reopened.load_events_for_run(run_id)

        assert reopened.load_workflow(workflow.id) == workflow
        assert reopened_run is not None
        assert reopened_run["id"] == run_id
        assert reopened_run["status"] == "RUNNING"
        assert reopened_run["paused"] == 1
        assert reopened_run["paused_at"] is not None
        assert json.loads(str(reopened_run["snapshot_json"])) == first_snapshot
        assert reopened_task is not None
        assert reopened_task["id"] == task_run_id
        assert reopened_task["status"] == "RUNNING"
        assert reopened_task["thread_id"] == "thread-reopen"
        assert reopened_task["turn_id"] == "turn-reopen"
        assert reopened_attempt["id"] == attempt_id
        assert reopened_attempt["status"] == "RUNNING"
        assert reopened_attempt["thread_id"] == "thread-reopen"
        assert reopened_attempt["turn_id"] == "turn-reopen"
        assert [event["event_type"] for event in events] == ["FIRST", "SECOND"]
        assert events[-1]["id"] == second_event_id
        assert [json.loads(event["payload_json"])["sequence"] for event in events] == [1, 2]
    finally:
        reopened_connection.close()
