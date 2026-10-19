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


def configured_app(tmp_path: Path) -> FastAPI:
    return create_app(ServiceConfig.from_db_path(tmp_path / "api.sqlite3"), adapter=FakeCodexAdapter())


def test_pause_route_returns_control_result(tmp_path: Path) -> None:
    app = configured_app(tmp_path)
    command = ControlCommand(run_id="run-1", action=ControlAction.PAUSE)

    with TestClient(app) as client:
        runtime = app.state.runtime
        runtime.pause = AsyncMock(return_value=accepted_result(command))  # type: ignore[method-assign]
        response = client.post("/api/runs/run-1/pause")

    assert response.status_code == 200
    assert response.json() == {
        "action": "PAUSE",
        "run_id": "run-1",
        "task_id": None,
        "accepted": True,
        "previous_status": None,
        "status": None,
        "retry_requested": False,
        "error_code": None,
        "message": None,
    }
    runtime.pause.assert_awaited_once_with("run-1")


def test_pause_route_maps_not_found_to_stable_error_envelope(tmp_path: Path) -> None:
    app = configured_app(tmp_path)
    command = ControlCommand(run_id="missing", action=ControlAction.PAUSE)

    with TestClient(app) as client:
        runtime = app.state.runtime
        runtime.pause = AsyncMock(
            return_value=rejected_result(command, error_code="RUN_NOT_FOUND", message="run not found")
        )  # type: ignore[method-assign]
        response = client.post("/api/runs/missing/pause")

    assert response.status_code == 404
    assert response.json() == {
        "detail": {"error": {"code": "CONTROL_RUN_NOT_FOUND", "message": "run not found"}}
    }


def test_pause_route_maps_conflict_and_invalid_action(tmp_path: Path) -> None:
    app = configured_app(tmp_path)
    command = ControlCommand(run_id="run-1", action=ControlAction.PAUSE)

    with TestClient(app) as client:
        runtime = app.state.runtime
        runtime.pause = AsyncMock(
            return_value=rejected_result(command, error_code="RUN_NOT_ACTIVE", message="terminal")
        )  # type: ignore[method-assign]
        conflict_response = client.post("/api/runs/run-1/pause")
        runtime.pause = AsyncMock(side_effect=ValueError("invalid control"))  # type: ignore[method-assign]
        invalid_response = client.post("/api/runs/run-1/pause")
    assert conflict_response.status_code == 409
    assert conflict_response.json()["detail"]["error"]["code"] == "CONTROL_CONFLICT"
    assert invalid_response.status_code == 422
    assert invalid_response.json()["detail"]["error"]["code"] == "INVALID_CONTROL_ACTION"
