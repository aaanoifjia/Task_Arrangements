import pytest

from codex_flow.domain.status import TaskStatus
from codex_flow.scheduler.actions import ManualAction, ManualActionError, SchedulerActions


def test_retry_reports_an_explicit_new_attempt_request() -> None:
    actions = SchedulerActions({"task": TaskStatus.FAILED})

    result = actions.retry("task")

    assert result.action is ManualAction.RETRY
    assert result.retry_requested is True
    assert result.status is TaskStatus.FAILED


@pytest.mark.parametrize(
    ("operation", "initial", "expected"),
    [
        ("cancel", TaskStatus.READY, TaskStatus.CANCELLED),
        ("skip", TaskStatus.BLOCKED, TaskStatus.SKIPPED),
        ("mark_success", TaskStatus.READY, TaskStatus.SUCCESS),
    ],
)
def test_state_actions_apply_only_explicit_valid_transitions(
    operation: str, initial: TaskStatus, expected: TaskStatus
) -> None:
    statuses = {"task": initial}
    actions = SchedulerActions(statuses)

    result = getattr(actions, operation)("task")

    assert result.status is expected
    assert statuses["task"] is expected


def test_pause_and_resume_report_their_result() -> None:
    actions = SchedulerActions({})

    pause = actions.pause_workflow()
    resume = actions.resume_workflow()

    assert pause.action is ManualAction.PAUSE_WORKFLOW
    assert resume.action is ManualAction.RESUME_WORKFLOW
    assert actions.paused is False


def test_invalid_actions_raise_explicit_errors() -> None:
    actions = SchedulerActions({"task": TaskStatus.SUCCESS})

    with pytest.raises(ManualActionError, match="retry"):
        actions.retry("task")
    with pytest.raises(ManualActionError, match="unknown task"):
        actions.cancel("missing")
    with pytest.raises(ManualActionError, match="not paused"):
        actions.resume_workflow()
