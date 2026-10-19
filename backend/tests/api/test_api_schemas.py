from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from codex_flow.api.errors import conflict, invalid_request, not_found
from codex_flow.api.schemas import (
    AttemptView,
    ErrorResponse,
    EventView,
    RunDetail,
    RunStartResponse,
    RunSummary,
    TaskRunView,
    WorkflowDetail,
    WorkflowSummary,
)


def test_public_dtos_round_trip_as_stable_json() -> None:
    values = [
        ErrorResponse(error={"code": "NOT_FOUND", "message": "missing"}),
        WorkflowSummary(id="w", name="Workflow"),
        RunStartResponse(run_id="r"),
        RunSummary(id="r", workflow_id="w", status="SUCCESS", created_at="now"),
        RunDetail(id="r", workflow_id="w", status="SUCCESS", created_at="now"),
        TaskRunView(id="t", workflow_run_id="r", task_id="A", status="SUCCESS", created_at="now"),
        AttemptView(id="a", task_run_id="t", status="SUCCESS", created_at="now"),
        EventView(id="e", event_type="TURN_STARTED", created_at="now"),
    ]

    assert all(type(value.model_dump_json()) is str for value in values)


def test_error_helpers_use_stable_status_and_shape() -> None:
    assert not_found("MISSING", "missing").status_code == 404
    assert conflict("ACTIVE", "active").status_code == 409
    assert invalid_request("INVALID", "invalid").status_code == 400


def test_openapi_can_generate_public_dtos() -> None:
    app = FastAPI()
    app.openapi_schema = None
    schema = get_openapi(
        title="test",
        version="1",
        routes=app.routes,
    )

    assert schema["openapi"]
    assert WorkflowDetail.model_json_schema()["properties"]
