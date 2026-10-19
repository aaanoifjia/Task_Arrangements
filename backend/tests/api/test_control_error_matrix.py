from pathlib import Path
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig
from codex_flow.api.errors import unprocessable
from codex_flow.application.control_contract import ControlAction, ControlCommand, rejected_result
from codex_flow.codex_adapter.fake import FakeCodexAdapter


def configured_app(tmp_path: Path) -> FastAPI:
    return create_app(ServiceConfig.from_db_path(tmp_path / "api.sqlite3"), adapter=FakeCodexAdapter())


def test_unknown_run_and_task_use_stable_not_found_codes(tmp_path: Path) -> None:
    app = configured_app(tmp_path)

    with TestClient(app) as client:
        missing_run = client.post("/api/runs/missing/pause")
        missing_task = client.post("/api/runs/missing/tasks/task/retry")

    assert missing_run.status_code == 404
    assert missing_run.json()["detail"]["error"]["code"] == "CONTROL_RUN_NOT_FOUND"
    assert missing_task.status_code == 404
    assert missing_task.json()["detail"]["error"]["code"] == "CONTROL_TASK_NOT_FOUND"


def test_invalid_state_and_interrupt_failure_are_stable_and_sanitized(tmp_path: Path) -> None:
    app = configured_app(tmp_path)
    command = ControlCommand(run_id="run-1", action=ControlAction.SKIP, task_id="task-1")

    with TestClient(app) as client:
        runtime = app.state.runtime
        runtime.skip = AsyncMock(
            return_value=rejected_result(command, error_code="TASK_NOT_SKIPPABLE", message="task is running")
        )  # type: ignore[method-assign]
        invalid = client.post("/api/runs/run-1/tasks/task-1/skip")
        runtime.cancel = AsyncMock(
            return_value=rejected_result(
                ControlCommand(run_id="run-1", action=ControlAction.CANCEL, task_id="task-1"),
                error_code="INTERRUPT_FAILED",
                message="interrupt failed",
            )
        )  # type: ignore[method-assign]
        interrupt = client.post("/api/runs/run-1/tasks/task-1/cancel")

    assert invalid.status_code == 422
    assert invalid.json()["detail"]["error"]["code"] == "INVALID_CONTROL_ACTION"
    assert interrupt.status_code == 409
    assert interrupt.json()["detail"]["error"]["code"] == "CONTROL_CONFLICT"
    assert "Traceback" not in interrupt.text
    assert "sdk" not in interrupt.text.lower()


def test_paused_conflicts_and_runtime_unavailable_use_stable_envelopes(tmp_path: Path) -> None:
    app = configured_app(tmp_path)
    command = ControlCommand(run_id="run-1", action=ControlAction.RESUME)

    with TestClient(app) as client:
        runtime = app.state.runtime
        runtime.resume = AsyncMock(
            return_value=rejected_result(command, error_code="NOT_PAUSED", message="run is not paused")
        )  # type: ignore[method-assign]
        not_paused = client.post("/api/runs/run-1/resume")
        app.state.runtime = None
        unavailable = client.post("/api/runs/run-1/pause")

    assert not_paused.status_code == 409
    assert not_paused.json()["detail"]["error"]["code"] == "CONTROL_CONFLICT"
    assert unavailable.status_code == 503
    assert unavailable.json()["detail"]["error"]["code"] == "RUNTIME_UNAVAILABLE"


def test_unprocessable_helper_preserves_the_public_error_shape() -> None:
    error = unprocessable("INVALID_CONTROL_ACTION", "invalid state")

    assert error.status_code == 422
    assert error.detail == {
        "error": {"code": "INVALID_CONTROL_ACTION", "message": "invalid state"}
    }
