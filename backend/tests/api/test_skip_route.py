from pathlib import Path
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig
from codex_flow.application.control_contract import (
    ControlAction,
    ControlCommand,
    accepted_result,
    rejected_result,
)
from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.domain.status import TaskStatus


def configured_app(tmp_path: Path) -> FastAPI:
    return create_app(ServiceConfig.from_db_path(tmp_path / "api.sqlite3"), adapter=FakeCodexAdapter())


def test_skip_route_returns_skipped_result(tmp_path: Path) -> None:
    app = configured_app(tmp_path)
    command = ControlCommand(run_id="run-1", action=ControlAction.SKIP, task_id="task-1")

    with TestClient(app) as client:
        runtime = app.state.runtime
        runtime.skip = AsyncMock(
            return_value=accepted_result(command, previous_status=TaskStatus.BLOCKED)
        )  # type: ignore[method-assign]
        response = client.post("/api/runs/run-1/tasks/task-1/skip")

    assert response.status_code == 200
    assert response.json()["status"] == "SKIPPED"
    assert response.json()["previous_status"] == "BLOCKED"
    runtime.skip.assert_awaited_once_with("run-1", "task-1")


def test_skip_route_exposes_stable_invalid_state_error(tmp_path: Path) -> None:
    app = configured_app(tmp_path)
    command = ControlCommand(run_id="run-1", action=ControlAction.SKIP, task_id="task-1")

    with TestClient(app) as client:
        runtime = app.state.runtime
        runtime.skip = AsyncMock(
            return_value=rejected_result(command, error_code="TASK_NOT_SKIPPABLE", message="task is running")
        )  # type: ignore[method-assign]
        response = client.post("/api/runs/run-1/tasks/task-1/skip")

    assert response.status_code == 422
    assert response.json() == {
        "detail": {"error": {"code": "INVALID_CONTROL_ACTION", "message": "task is running"}}
    }
