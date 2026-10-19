"""Explicit manual controls for scheduler task states."""

from collections.abc import MutableMapping
from dataclasses import dataclass
from enum import StrEnum

from codex_flow.domain.status import TaskStatus
from codex_flow.scheduler.state_machine import TransitionTrigger, transition


class ManualActionError(ValueError):
    """Raised when an explicit action cannot be safely applied."""


class ManualAction(StrEnum):
    RETRY = "RETRY"
    CANCEL = "CANCEL"
    SKIP = "SKIP"
    MARK_SUCCESS = "MARK_SUCCESS"
    PAUSE_WORKFLOW = "PAUSE_WORKFLOW"
    RESUME_WORKFLOW = "RESUME_WORKFLOW"


@dataclass(frozen=True)
class ManualActionResult:
    action: ManualAction
    task_id: str | None
    previous_status: TaskStatus | None
    status: TaskStatus | None
    retry_requested: bool = False


class SchedulerActions:
    """Apply only valid user actions and expose each result to the caller."""

    def __init__(self, statuses: MutableMapping[str, TaskStatus]) -> None:
        self._statuses = statuses
        self.paused = False

    def retry(self, task_id: str) -> ManualActionResult:
        status = self._require_status(task_id)
        if status not in {TaskStatus.FAILED, TaskStatus.INTERRUPTED, TaskStatus.NEEDS_ATTENTION}:
            raise ManualActionError(f"retry is not allowed from {status}")
        return ManualActionResult(ManualAction.RETRY, task_id, status, status, retry_requested=True)

    def cancel(self, task_id: str) -> ManualActionResult:
        return self._transition(task_id, TaskStatus.CANCELLED)

    def skip(self, task_id: str) -> ManualActionResult:
        return self._transition(task_id, TaskStatus.SKIPPED)

    def mark_success(self, task_id: str) -> ManualActionResult:
        return self._transition(task_id, TaskStatus.SUCCESS)

    def pause_workflow(self) -> ManualActionResult:
        if self.paused:
            raise ManualActionError("workflow is already paused")
        self.paused = True
        return ManualActionResult(ManualAction.PAUSE_WORKFLOW, None, None, None)

    def resume_workflow(self) -> ManualActionResult:
        if not self.paused:
            raise ManualActionError("workflow is not paused")
        self.paused = False
        return ManualActionResult(ManualAction.RESUME_WORKFLOW, None, None, None)

    def _require_status(self, task_id: str) -> TaskStatus:
        try:
            return self._statuses[task_id]
        except KeyError as error:
            raise ManualActionError(f"unknown task: {task_id}") from error

    def _transition(self, task_id: str, target: TaskStatus) -> ManualActionResult:
        current = self._require_status(task_id)
        try:
            updated = transition(current, target, TransitionTrigger.USER_ACTION)
        except ValueError as error:
            raise ManualActionError(str(error)) from error
        self._statuses[task_id] = updated
        action = {
            TaskStatus.CANCELLED: ManualAction.CANCEL,
            TaskStatus.SKIPPED: ManualAction.SKIP,
            TaskStatus.SUCCESS: ManualAction.MARK_SUCCESS,
        }[target]
        return ManualActionResult(action, task_id, current, updated)
