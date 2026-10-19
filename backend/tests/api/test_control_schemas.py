from codex_flow.api.schemas import ManualActionResponse, RunControlState
from codex_flow.application.control_contract import (
    ControlAction,
    ControlCommand,
    accepted_result,
    rejected_result,
)
from codex_flow.domain.status import TaskStatus


def test_manual_action_response_serializes_accept_and_retry_without_sdk_objects() -> None:
    command = ControlCommand(run_id="run-1", action=ControlAction.RETRY, task_id="task-1")
    response = ManualActionResponse.model_validate(
        accepted_result(command, previous_status=TaskStatus.FAILED).model_dump()
    )

    assert response.model_dump()["action"] == ControlAction.RETRY
    assert response.retry_requested is True
    assert response.status is None
    assert "openai_codex" not in str(ManualActionResponse.model_json_schema())


def test_manual_action_response_serializes_rejection() -> None:
    command = ControlCommand(run_id="run-1", action=ControlAction.PAUSE)
    response = ManualActionResponse.model_validate(
        rejected_result(command, error_code="RUN_NOT_ACTIVE", message="terminal").model_dump()
    )

    assert response.accepted is False
    assert response.error_code == "RUN_NOT_ACTIVE"
    assert response.message == "terminal"


def test_run_control_state_is_durable_and_sdk_independent() -> None:
    state = RunControlState(run_id="run-1", paused=True, paused_at="2026-10-20T00:00:00Z")

    assert state.model_dump() == {
        "run_id": "run-1",
        "paused": True,
        "paused_at": "2026-10-20T00:00:00Z",
    }
