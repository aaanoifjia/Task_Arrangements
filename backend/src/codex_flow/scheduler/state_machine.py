from enum import StrEnum

from codex_flow.domain.status import TaskStatus


class TransitionError(ValueError):
    pass


class TransitionTrigger(StrEnum):
    DEPENDENCY_EVALUATION = "DEPENDENCY_EVALUATION"
    SCHEDULER = "SCHEDULER"
    CODEX_EVENT = "CODEX_EVENT"
    USER_ACTION = "USER_ACTION"
    RECOVERY = "RECOVERY"


_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.PENDING: frozenset({TaskStatus.READY, TaskStatus.BLOCKED, TaskStatus.CANCELLED}),
    TaskStatus.BLOCKED: frozenset({TaskStatus.READY, TaskStatus.CANCELLED, TaskStatus.SKIPPED}),
    TaskStatus.READY: frozenset({TaskStatus.STARTING, TaskStatus.CANCELLED, TaskStatus.SKIPPED, TaskStatus.SUCCESS}),
    TaskStatus.STARTING: frozenset({TaskStatus.RUNNING, TaskStatus.FAILED, TaskStatus.CANCELLED}),
    TaskStatus.RUNNING: frozenset({TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.INTERRUPTED, TaskStatus.NEEDS_ATTENTION, TaskStatus.CANCELLED}),
    TaskStatus.NEEDS_ATTENTION: frozenset({TaskStatus.RUNNING, TaskStatus.FAILED, TaskStatus.CANCELLED}),
    TaskStatus.SUCCESS: frozenset(),
    TaskStatus.FAILED: frozenset(),
    TaskStatus.INTERRUPTED: frozenset(),
    TaskStatus.SKIPPED: frozenset(),
    TaskStatus.CANCELLED: frozenset(),
}

_TRIGGER_TRANSITIONS: dict[TransitionTrigger, frozenset[tuple[TaskStatus, TaskStatus]]] = {
    TransitionTrigger.DEPENDENCY_EVALUATION: frozenset(
        {(TaskStatus.PENDING, TaskStatus.READY), (TaskStatus.PENDING, TaskStatus.BLOCKED), (TaskStatus.BLOCKED, TaskStatus.READY)}
    ),
    TransitionTrigger.SCHEDULER: frozenset({(TaskStatus.READY, TaskStatus.STARTING)}),
    TransitionTrigger.CODEX_EVENT: frozenset(
        {
            (TaskStatus.STARTING, TaskStatus.RUNNING),
            (TaskStatus.STARTING, TaskStatus.FAILED),
            (TaskStatus.RUNNING, TaskStatus.SUCCESS),
            (TaskStatus.RUNNING, TaskStatus.FAILED),
            (TaskStatus.RUNNING, TaskStatus.INTERRUPTED),
            (TaskStatus.RUNNING, TaskStatus.NEEDS_ATTENTION),
            (TaskStatus.NEEDS_ATTENTION, TaskStatus.RUNNING),
            (TaskStatus.NEEDS_ATTENTION, TaskStatus.FAILED),
        }
    ),
    TransitionTrigger.USER_ACTION: frozenset(
        {
            (TaskStatus.PENDING, TaskStatus.CANCELLED),
            (TaskStatus.BLOCKED, TaskStatus.CANCELLED),
            (TaskStatus.BLOCKED, TaskStatus.SKIPPED),
            (TaskStatus.READY, TaskStatus.CANCELLED),
            (TaskStatus.READY, TaskStatus.SKIPPED),
            (TaskStatus.READY, TaskStatus.SUCCESS),
            (TaskStatus.STARTING, TaskStatus.CANCELLED),
            (TaskStatus.RUNNING, TaskStatus.CANCELLED),
            (TaskStatus.NEEDS_ATTENTION, TaskStatus.CANCELLED),
        }
    ),
    TransitionTrigger.RECOVERY: frozenset(
        {
            (TaskStatus.STARTING, TaskStatus.RUNNING),
            (TaskStatus.STARTING, TaskStatus.FAILED),
            (TaskStatus.RUNNING, TaskStatus.SUCCESS),
            (TaskStatus.RUNNING, TaskStatus.FAILED),
            (TaskStatus.RUNNING, TaskStatus.INTERRUPTED),
            (TaskStatus.RUNNING, TaskStatus.NEEDS_ATTENTION),
            (TaskStatus.NEEDS_ATTENTION, TaskStatus.RUNNING),
            (TaskStatus.NEEDS_ATTENTION, TaskStatus.FAILED),
        }
    ),
}


def transition(current: TaskStatus, target: TaskStatus, trigger: TransitionTrigger) -> TaskStatus:
    pair = (current, target)
    if target not in _TRANSITIONS[current]:
        raise TransitionError(f"invalid transition: {current} -> {target}")
    if pair not in _TRIGGER_TRANSITIONS[trigger]:
        raise TransitionError(f"invalid trigger {trigger} for {current} -> {target}")
    return target


def requires_audit_event(current: TaskStatus, target: TaskStatus, trigger: TransitionTrigger) -> bool:
    return trigger is TransitionTrigger.USER_ACTION and (current, target) in {
        (TaskStatus.BLOCKED, TaskStatus.SKIPPED),
        (TaskStatus.READY, TaskStatus.SKIPPED),
        (TaskStatus.READY, TaskStatus.SUCCESS),
    }
