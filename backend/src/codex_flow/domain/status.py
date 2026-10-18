from enum import StrEnum


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"
    READY = "READY"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    INTERRUPTED = "INTERRUPTED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


TERMINAL_STATUSES: frozenset[TaskStatus] = frozenset(
    {
        TaskStatus.SUCCESS,
        TaskStatus.FAILED,
        TaskStatus.INTERRUPTED,
        TaskStatus.SKIPPED,
        TaskStatus.CANCELLED,
    }
)


def is_terminal(status: TaskStatus) -> bool:
    return status in TERMINAL_STATUSES
