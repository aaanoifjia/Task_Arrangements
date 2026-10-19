"""Application boundary for durable manual control operations."""

from collections.abc import Awaitable, Callable
from typing import NoReturn

from codex_flow.application.control_contract import (
    ControlAction,
    ControlCommand,
    ControlResult,
)
from codex_flow.runtime.manager import RuntimeManager


class ControlServiceError(ValueError):
    """Base error exposed by the control application boundary."""

    code = "CONTROL_ERROR"


class ControlNotFoundError(ControlServiceError):
    code = "NOT_FOUND"


class ControlConflictError(ControlServiceError):
    code = "CONFLICT"


class InvalidControlActionError(ControlServiceError):
    code = "INVALID_ACTION"


class ControlApplicationService:
    """Translate stable control commands into runtime operations."""

    def __init__(self, runtime: RuntimeManager) -> None:
        self._runtime = runtime

    async def apply(self, command: ControlCommand) -> ControlResult:
        try:
            result = await self._dispatch(command)
        except RuntimeError as error:
            raise ControlConflictError(str(error)) from error
        except (KeyError, ValueError) as error:
            raise InvalidControlActionError(str(error)) from error
        if result.accepted:
            return result
        self._raise_rejected(result)

    async def _dispatch(self, command: ControlCommand) -> ControlResult:
        operations: dict[ControlAction, Callable[..., Awaitable[ControlResult]]] = {
            ControlAction.PAUSE: self._runtime.pause,
            ControlAction.RESUME: self._runtime.resume,
            ControlAction.RETRY: self._runtime.retry,
            ControlAction.CANCEL: self._runtime.cancel,
            ControlAction.SKIP: self._runtime.skip,
            ControlAction.MARK_SUCCESS: self._runtime.mark_success,
        }
        operation = operations[command.action]
        if command.action in {ControlAction.PAUSE, ControlAction.RESUME}:
            return await operation(command.run_id)
        if command.task_id is None:
            raise InvalidControlActionError(f"{command.action} requires task_id")
        return await operation(command.run_id, command.task_id)

    @staticmethod
    def _raise_rejected(result: ControlResult) -> NoReturn:
        code = result.error_code or "INVALID_ACTION"
        message = result.message or "control action was rejected"
        if code in {"RUN_NOT_FOUND", "TASK_NOT_FOUND"}:
            raise ControlNotFoundError(message)
        if code in {
            "RUN_NOT_ACTIVE",
            "ALREADY_PAUSED",
            "NOT_PAUSED",
            "STALE_STATE",
            "EXTERNAL_STATE_UNKNOWN",
            "INTERRUPT_FAILED",
        }:
            raise ControlConflictError(message)
        raise InvalidControlActionError(message)
