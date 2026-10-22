"""WebSocket cursor and snapshot continuity across API app recreation."""

from pathlib import Path

from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def _prepare_run(database: Path) -> tuple[str, str, str, str]:
    workflow = WorkflowDefinition(
        id="ws-restart-workflow",
        name="WebSocket Restart Workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".")],
        edges=[],
    )
    connection = open_database(database)
    try:
        repository = StorageRepositories(connection)
        repository.save_workflow_definition(workflow)
        run_id = repository.create_workflow_run(
            workflow.id, workflow.model_dump(mode="json")
        )
        task_run_id = repository.create_task_runs(run_id, ["A"])[0]
        first_event_id = repository.append_event(
            "FIRST", {"sequence": 1}, workflow_run_id=run_id, task_run_id=task_run_id
        )
        second_event_id = repository.append_event(
            "SECOND", {"sequence": 2}, workflow_run_id=run_id, task_run_id=task_run_id
        )
    finally:
        connection.close()
    return run_id, task_run_id, first_event_id, second_event_id


def test_websocket_resume_after_app_recreation_has_only_post_cursor_events(
    tmp_path: Path,
) -> None:
    database = tmp_path / "ws-restart.sqlite3"
    run_id, task_run_id, first_event_id, second_event_id = _prepare_run(database)
    config = ServiceConfig(db_path=database, event_poll_interval_seconds=0)

    with TestClient(create_app(config)) as client:
        with client.websocket_connect(f"/ws/runs/{run_id}") as socket:
            first = socket.receive_json()
            second = socket.receive_json()
        assert first["kind"] == "event"
        assert first["payload"]["id"] == first_event_id
        assert second["kind"] == "event"
        assert second["payload"]["id"] == second_event_id

    connection = open_database(database)
    try:
        repository = StorageRepositories(connection)
        third_event_id = repository.append_event(
            "THIRD", {"sequence": 3}, workflow_run_id=run_id, task_run_id=task_run_id
        )
        repository.update_task_run_state(task_run_id, "SUCCESS")
        repository.update_workflow_run_state(run_id, "SUCCESS")
    finally:
        connection.close()

    with TestClient(create_app(config)) as client, client.websocket_connect(
        f"/ws/runs/{run_id}?after={second_event_id}"
    ) as socket:
        event = socket.receive_json()
        snapshot = socket.receive_json()

    assert event["kind"] == "event"
    assert event["payload"]["id"] == third_event_id
    assert event["payload"]["event_type"] == "THIRD"
    assert snapshot["kind"] == "snapshot"
    assert snapshot["payload"]["tasks"][0]["status"] == "SUCCESS"
