from pathlib import Path
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig
from codex_flow.application.control_contract import ControlAction, ControlCommand, accepted_result
from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def configured_app(tmp_path: Path) -> tuple[FastAPI, str, str]:
    db_path = tmp_path / "api.sqlite3"
    connection = open_database(db_path)
    repository = StorageRepositories(connection)
    workflow = WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".")],
        edges=[],
    )
    repository.save_workflow_definition(workflow)
    workflow_run_id = repository.create_workflow_run("workflow", workflow.model_dump())
    task_run_id = repository.create_task_runs(workflow_run_id, ["A"])[0]
    connection.close()
    return create_app(ServiceConfig.from_db_path(db_path), adapter=FakeCodexAdapter()), workflow_run_id, task_run_id


def test_retry_route_resolves_public_task_id_to_task_run_id(tmp_path: Path) -> None:
    app, run_id, task_run_id = configured_app(tmp_path)

    with TestClient(app) as client:
        command = ControlCommand(run_id=run_id, action=ControlAction.RETRY, task_id=task_run_id)
        runtime = app.state.runtime
        runtime.retry = AsyncMock(return_value=accepted_result(command, previous_status="FAILED"))  # type: ignore[method-assign,arg-type]

        response = client.post(f"/api/runs/{run_id}/tasks/A/retry")

    assert response.status_code == 200
    assert response.json()["action"] == "RETRY"
    assert response.json()["task_id"] == task_run_id
    runtime.retry.assert_awaited_once_with(run_id, task_run_id)


def test_retry_route_accepts_task_run_id_directly(tmp_path: Path) -> None:
    app, run_id, task_run_id = configured_app(tmp_path)

    with TestClient(app) as client:
        command = ControlCommand(run_id=run_id, action=ControlAction.RETRY, task_id=task_run_id)
        runtime = app.state.runtime
        runtime.retry = AsyncMock(return_value=accepted_result(command, previous_status="FAILED"))  # type: ignore[method-assign,arg-type]

        response = client.post(f"/api/runs/{run_id}/tasks/{task_run_id}/retry")

    assert response.status_code == 200
    runtime.retry.assert_awaited_once_with(run_id, task_run_id)
