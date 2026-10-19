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


def test_resume_route_returns_continuation_request(tmp_path: Path) -> None:
    app = configured_app(tmp_path)
    command = ControlCommand(run_id="run-1", action=ControlAction.RESUME)

    with TestClient(app) as client:
        runtime = app.state.runtime
        runtime.resume = AsyncMock(return_value=accepted_result(command))  # type: ignore[method-assign]
        response = client.post("/api/runs/run-1/resume")

    assert response.status_code == 200
    assert response.json()["action"] == "RESUME"
    assert response.json()["accepted"] is True
    runtime.resume.assert_awaited_once_with("run-1")


def test_resume_route_maps_not_paused_to_conflict_envelope(tmp_path: Path) -> None:
    app = configured_app(tmp_path)
    command = ControlCommand(run_id="run-1", action=ControlAction.RESUME)

    with TestClient(app) as client:
        runtime = app.state.runtime
        runtime.resume = AsyncMock(
            return_value=rejected_result(command, error_code="NOT_PAUSED", message="run is not paused")
        )  # type: ignore[method-assign]
        response = client.post("/api/runs/run-1/resume")

    assert response.status_code == 409
    assert response.json() == {
        "detail": {"error": {"code": "CONTROL_CONFLICT", "message": "run is not paused"}}
    }
