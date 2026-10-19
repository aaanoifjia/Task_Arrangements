from unittest.mock import AsyncMock, Mock

import pytest

from codex_flow.application.control_contract import (
    ControlAction,
    ControlCommand,
    accepted_result,
    rejected_result,
)
from codex_flow.application.controls import (
    ControlApplicationService,
    ControlConflictError,
    ControlNotFoundError,
    InvalidControlActionError,
)
from codex_flow.domain.status import TaskStatus


def runtime_mock() -> Mock:
    runtime = Mock()
    for name in ("pause", "resume", "retry", "cancel", "skip", "mark_success"):
        setattr(runtime, name, AsyncMock())
    return runtime


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("action", "task_id", "previous"),
    [
        (ControlAction.PAUSE, None, None),
        (ControlAction.RESUME, None, None),
        (ControlAction.RETRY, "task-1", TaskStatus.FAILED),
        (ControlAction.CANCEL, "task-1", TaskStatus.READY),
        (ControlAction.SKIP, "task-1", TaskStatus.BLOCKED),
        (ControlAction.MARK_SUCCESS, "task-1", TaskStatus.READY),
    ],
)
async def test_service_dispatches_every_control_action(
    action: ControlAction, task_id: str | None, previous: TaskStatus | None
) -> None:
    runtime = runtime_mock()
    service = ControlApplicationService(runtime)  # type: ignore[arg-type]
    command = ControlCommand(run_id="run-1", action=action, task_id=task_id)
    runtime_result = accepted_result(command, previous_status=previous)
    getattr(runtime, action.value.lower() if action not in {ControlAction.MARK_SUCCESS} else "mark_success").return_value = runtime_result
    if action is ControlAction.PAUSE:
        runtime.pause.return_value = runtime_result
    elif action is ControlAction.RESUME:
        runtime.resume.return_value = runtime_result
    elif action is ControlAction.RETRY:
        runtime.retry.return_value = runtime_result
    elif action is ControlAction.CANCEL:
        runtime.cancel.return_value = runtime_result
    elif action is ControlAction.SKIP:
        runtime.skip.return_value = runtime_result
    else:
        runtime.mark_success.return_value = runtime_result

    result = await service.apply(command)

    assert result == runtime_result
    method = runtime.pause if action is ControlAction.PAUSE else runtime.resume if action is ControlAction.RESUME else runtime.retry if action is ControlAction.RETRY else runtime.cancel if action is ControlAction.CANCEL else runtime.skip if action is ControlAction.SKIP else runtime.mark_success
    if task_id is None:
        method.assert_awaited_once_with("run-1")
    else:
        method.assert_awaited_once_with("run-1", task_id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("code", "error_type"),
    [
        ("RUN_NOT_FOUND", ControlNotFoundError),
        ("STALE_STATE", ControlConflictError),
        ("TASK_NOT_MARKABLE", InvalidControlActionError),
    ],
)
async def test_service_translates_rejected_runtime_results(code: str, error_type: type[ValueError]) -> None:
    runtime = runtime_mock()
    command = ControlCommand(run_id="run-1", action=ControlAction.PAUSE)
    runtime.pause.return_value = rejected_result(command, error_code=code, message="rejected")

    with pytest.raises(error_type, match="rejected"):
        await ControlApplicationService(runtime).apply(command)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_service_translates_runtime_failures() -> None:
    runtime = runtime_mock()
    runtime.pause.side_effect = RuntimeError("runtime unavailable")
    command = ControlCommand(run_id="run-1", action=ControlAction.PAUSE)

    with pytest.raises(ControlConflictError, match="runtime unavailable"):
        await ControlApplicationService(runtime).apply(command)  # type: ignore[arg-type]
