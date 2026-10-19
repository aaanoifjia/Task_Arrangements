from pathlib import Path
from unittest.mock import AsyncMock

import pytest
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


def configured_app(tmp_path: Path, name: str = "api.sqlite3") -> FastAPI:
    return create_app(ServiceConfig.from_db_path(tmp_path / name), adapter=FakeCodexAdapter())


@pytest.mark.parametrize("previous_status", [TaskStatus.READY, TaskStatus.RUNNING])
def test_cancel_route_covers_queued_and_running_paths(
    tmp_path: Path, previous_status: TaskStatus
) -> None:
    app = configured_app(tmp_path, f"{previous_status.value}.sqlite3")
    command = ControlCommand(run_id="run-1", action=ControlAction.CANCEL, task_id="task-1")

    with TestClient(app) as client:
        runtime = app.state.runtime
        runtime.cancel = AsyncMock(  # type: ignore[method-assign]
            return_value=accepted_result(command, previous_status=previous_status)
        )
        response = client.post("/api/runs/run-1/tasks/task-1/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"
    assert response.json()["previous_status"] == previous_status.value
    runtime.cancel.assert_awaited_once_with("run-1", "task-1")


def test_cancel_route_maps_active_turn_conflict(tmp_path: Path) -> None:
    app = configured_app(tmp_path)
    command = ControlCommand(run_id="run-1", action=ControlAction.CANCEL, task_id="task-1")

    with TestClient(app) as client:
        runtime = app.state.runtime
        runtime.cancel = AsyncMock(
            return_value=rejected_result(command, error_code="INTERRUPT_FAILED", message="interrupt failed")
        )  # type: ignore[method-assign]
        response = client.post("/api/runs/run-1/tasks/task-1/cancel")

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "CONTROL_CONFLICT"
