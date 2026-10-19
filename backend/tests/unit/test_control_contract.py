import pytest
from pydantic import ValidationError

from codex_flow.application.control_contract import (
    ControlAction,
    ControlCommand,
    ControlResult,
    accepted_result,
    rejected_result,
)
from codex_flow.domain.status import TaskStatus


@pytest.mark.parametrize("action", [ControlAction.PAUSE, ControlAction.RESUME])
def test_workflow_controls_are_run_scoped(action: ControlAction) -> None:
    command = ControlCommand(run_id="run-1", action=action)
    assert command.task_id is None
    assert accepted_result(command).model_dump() == {
        "action": action,
        "run_id": "run-1",
        "task_id": None,
        "accepted": True,
        "previous_status": None,
        "status": None,
        "retry_requested": False,
        "error_code": None,
        "message": None,
    }


@pytest.mark.parametrize(
    ("action", "target"),
    [
        (ControlAction.CANCEL, TaskStatus.CANCELLED),
        (ControlAction.SKIP, TaskStatus.SKIPPED),
        (ControlAction.MARK_SUCCESS, TaskStatus.SUCCESS),
    ],
)
def test_task_controls_report_frozen_target_status(
    action: ControlAction, target: TaskStatus
) -> None:
    result = accepted_result(
        ControlCommand(run_id="run-1", action=action, task_id="task-1"),
        previous_status=TaskStatus.READY,
    )
    assert result.status is target
    assert result.previous_status is TaskStatus.READY


def test_retry_is_a_new_attempt_request_not_a_status_transition() -> None:
    result = accepted_result(
        ControlCommand(run_id="run-1", action=ControlAction.RETRY, task_id="task-1"),
        previous_status=TaskStatus.FAILED,
    )
    assert result.retry_requested is True
    assert result.status is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"action": ControlAction.PAUSE, "task_id": "task-1"},
        {"action": ControlAction.RETRY},
        {"action": ControlAction.CANCEL},
        {"action": ControlAction.SKIP},
        {"action": ControlAction.MARK_SUCCESS},
    ],
)
def test_command_scope_validation_is_fail_closed(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ControlCommand(run_id="run-1", **kwargs)


def test_rejected_result_is_explicit_and_does_not_report_transition() -> None:
    command = ControlCommand(run_id="run-1", action=ControlAction.RETRY, task_id="task-1")
    result = rejected_result(command, error_code="INVALID_STATE", message="task is RUNNING")
    assert result.accepted is False
    assert result.status is None
    assert result.retry_requested is False


def test_result_rejects_inconsistent_retry_and_status_payloads() -> None:
    with pytest.raises(ValidationError, match="retry reports"):
        ControlResult(
            action=ControlAction.RETRY,
            run_id="run-1",
            task_id="task-1",
            accepted=True,
            previous_status=TaskStatus.FAILED,
            status=TaskStatus.PENDING,
            retry_requested=True,
        )


def test_commands_have_no_sdk_dependency() -> None:
    assert ControlCommand.model_config["extra"] == "forbid"
