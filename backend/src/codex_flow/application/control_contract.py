"""SDK-independent durable control commands and results."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from codex_flow.domain.status import TaskStatus


class ControlAction(StrEnum):
    """Manual operations accepted by the durable control boundary."""

    PAUSE = "PAUSE"
    RESUME = "RESUME"
    RETRY = "RETRY"
    CANCEL = "CANCEL"
    SKIP = "SKIP"
    MARK_SUCCESS = "MARK_SUCCESS"


WORKFLOW_ACTIONS: frozenset[ControlAction] = frozenset(
    {ControlAction.PAUSE, ControlAction.RESUME}
)
TASK_ACTIONS: frozenset[ControlAction] = frozenset(
    {
        ControlAction.RETRY,
        ControlAction.CANCEL,
        ControlAction.SKIP,
        ControlAction.MARK_SUCCESS,
    }
)
TARGET_STATUSES: dict[ControlAction, TaskStatus] = {
    ControlAction.CANCEL: TaskStatus.CANCELLED,
    ControlAction.SKIP: TaskStatus.SKIPPED,
    ControlAction.MARK_SUCCESS: TaskStatus.SUCCESS,
}


class ControlContractError(ValueError):
    """Raised when a control command or result violates the durable contract."""


class ControlCommand(BaseModel):
    """A validated run-level or task-level manual control request."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str
    action: ControlAction
    task_id: str | None = None

    @field_validator("run_id", "task_id")
    @classmethod
    def must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("must not be blank")
        return value

    @model_validator(mode="after")
    def validate_scope(self) -> "ControlCommand":
        if self.action in WORKFLOW_ACTIONS and self.task_id is not None:
            raise ValueError(f"{self.action} is a workflow-level action")
        if self.action in TASK_ACTIONS and self.task_id is None:
            raise ValueError(f"{self.action} requires task_id")
        return self


class ControlResult(BaseModel):
    """The deterministic result of accepting or rejecting a control command."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    action: ControlAction
    run_id: str
    task_id: str | None = None
    accepted: bool
    previous_status: TaskStatus | None = None
    status: TaskStatus | None = None
    retry_requested: bool = False
    error_code: str | None = None
    message: str | None = None

    @field_validator("run_id", "task_id", "error_code", "message")
    @classmethod
    def optional_text_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("must not be blank")
        return value

    @model_validator(mode="after")
    def validate_result(self) -> "ControlResult":
        ControlCommand(run_id=self.run_id, action=self.action, task_id=self.task_id)
        if not self.accepted:
            if self.error_code is None or self.message is None:
                raise ValueError("rejected controls require error_code and message")
            if self.status is not None or self.retry_requested:
                raise ValueError("rejected controls cannot report a target result")
            return self

        if self.error_code is not None or self.message is not None:
            raise ValueError("accepted controls cannot report an error")
        if self.action in WORKFLOW_ACTIONS:
            if self.previous_status is not None or self.status is not None:
                raise ValueError("workflow controls do not carry task statuses")
            if self.retry_requested:
                raise ValueError("workflow controls cannot request retry")
            return self

        if self.previous_status is None:
            raise ValueError("accepted task controls require previous_status")
        if self.action is ControlAction.RETRY:
            if not self.retry_requested or self.status is not None:
                raise ValueError("retry reports a new-attempt request, not a status transition")
            return self
        if self.retry_requested or self.status is not TARGET_STATUSES[self.action]:
            raise ValueError("control result target status is inconsistent with its action")
        return self


def accepted_result(
    command: ControlCommand,
    *,
    previous_status: TaskStatus | None = None,
) -> ControlResult:
    """Build the canonical accepted result for a validated command."""

    if command.action in WORKFLOW_ACTIONS:
        return ControlResult(
            action=command.action,
            run_id=command.run_id,
            accepted=True,
        )
    if command.action is ControlAction.RETRY:
        return ControlResult(
            action=command.action,
            run_id=command.run_id,
            task_id=command.task_id,
            accepted=True,
            previous_status=previous_status,
            retry_requested=True,
        )
    return ControlResult(
        action=command.action,
        run_id=command.run_id,
        task_id=command.task_id,
        accepted=True,
        previous_status=previous_status,
        status=TARGET_STATUSES[command.action],
    )


def rejected_result(command: ControlCommand, *, error_code: str, message: str) -> ControlResult:
    """Build the canonical rejected result without mutating durable state."""

    return ControlResult(
        action=command.action,
        run_id=command.run_id,
        task_id=command.task_id,
        accepted=False,
        error_code=error_code,
        message=message,
    )
