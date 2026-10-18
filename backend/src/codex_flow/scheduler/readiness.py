from collections.abc import Mapping
from enum import StrEnum

from codex_flow.domain.models import WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.scheduler.graph import dependency_map, topological_order


class ReadinessDecision(StrEnum):
    READY = "READY"
    BLOCKED = "BLOCKED"


def evaluate_task_readiness(dependency_statuses: list[TaskStatus]) -> ReadinessDecision:
    if all(status is TaskStatus.SUCCESS for status in dependency_statuses):
        return ReadinessDecision.READY
    return ReadinessDecision.BLOCKED


def ready_task_ids(workflow: WorkflowDefinition, statuses: Mapping[str, TaskStatus]) -> list[str]:
    order = topological_order(workflow)
    dependencies = dependency_map(workflow)
    missing = [task_id for task_id in order if task_id not in statuses]
    if missing:
        raise ValueError(f"missing task status: {missing[0]}")
    return [
        task_id
        for task_id in order
        if statuses[task_id] in {TaskStatus.PENDING, TaskStatus.BLOCKED}
        and evaluate_task_readiness([statuses[dependency] for dependency in dependencies[task_id]])
        is ReadinessDecision.READY
    ]
