import pytest

from codex_flow.domain.status import TERMINAL_STATUSES, TaskStatus, is_terminal
from codex_flow.scheduler.state_machine import (
    TransitionError,
    TransitionTrigger,
    requires_audit_event,
    transition,
)


def test_exact_status_and_terminal_sets() -> None:
    assert len(TaskStatus) == 11
    assert TERMINAL_STATUSES == {
        TaskStatus.SUCCESS,
        TaskStatus.FAILED,
        TaskStatus.INTERRUPTED,
        TaskStatus.SKIPPED,
        TaskStatus.CANCELLED,
    }
    assert is_terminal(TaskStatus.SUCCESS)
    assert not is_terminal(TaskStatus.RUNNING)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (TaskStatus.PENDING, TaskStatus.READY),
        (TaskStatus.PENDING, TaskStatus.BLOCKED),
        (TaskStatus.BLOCKED, TaskStatus.READY),
    ],
)
def test_dependency_transitions(current: TaskStatus, target: TaskStatus) -> None:
    assert transition(current, target, TransitionTrigger.DEPENDENCY_EVALUATION) is target


def test_scheduler_transition() -> None:
    assert transition(TaskStatus.READY, TaskStatus.STARTING, TransitionTrigger.SCHEDULER) is TaskStatus.STARTING


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (TaskStatus.STARTING, TaskStatus.RUNNING),
        (TaskStatus.STARTING, TaskStatus.FAILED),
        (TaskStatus.RUNNING, TaskStatus.SUCCESS),
        (TaskStatus.RUNNING, TaskStatus.FAILED),
        (TaskStatus.RUNNING, TaskStatus.INTERRUPTED),
        (TaskStatus.RUNNING, TaskStatus.NEEDS_ATTENTION),
        (TaskStatus.NEEDS_ATTENTION, TaskStatus.RUNNING),
        (TaskStatus.NEEDS_ATTENTION, TaskStatus.FAILED),
    ],
)
def test_codex_event_transitions(current: TaskStatus, target: TaskStatus) -> None:
    assert transition(current, target, TransitionTrigger.CODEX_EVENT) is target


def test_user_and_recovery_transitions() -> None:
    assert transition(TaskStatus.READY, TaskStatus.SKIPPED, TransitionTrigger.USER_ACTION) is TaskStatus.SKIPPED
    assert transition(TaskStatus.RUNNING, TaskStatus.SUCCESS, TransitionTrigger.RECOVERY) is TaskStatus.SUCCESS


def test_terminal_and_failed_retry_rejected() -> None:
    with pytest.raises(TransitionError, match="invalid transition"):
        transition(TaskStatus.SUCCESS, TaskStatus.READY, TransitionTrigger.USER_ACTION)
    with pytest.raises(TransitionError, match="invalid transition"):
        transition(TaskStatus.FAILED, TaskStatus.READY, TransitionTrigger.RECOVERY)


def test_wrong_trigger_rejected() -> None:
    with pytest.raises(TransitionError, match="invalid trigger"):
        transition(TaskStatus.READY, TaskStatus.STARTING, TransitionTrigger.USER_ACTION)


def test_audit_helper() -> None:
    assert requires_audit_event(TaskStatus.READY, TaskStatus.SUCCESS, TransitionTrigger.USER_ACTION)
    assert requires_audit_event(TaskStatus.BLOCKED, TaskStatus.SKIPPED, TransitionTrigger.USER_ACTION)
    assert not requires_audit_event(TaskStatus.READY, TaskStatus.SUCCESS, TransitionTrigger.CODEX_EVENT)
