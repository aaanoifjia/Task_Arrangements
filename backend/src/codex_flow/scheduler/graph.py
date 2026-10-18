from collections import defaultdict

from codex_flow.domain.models import WorkflowDefinition


class GraphValidationError(ValueError):
    pass


def validate_workflow(workflow: WorkflowDefinition) -> None:
    task_ids = [task.id for task in workflow.tasks]
    if len(task_ids) != len(set(task_ids)):
        raise GraphValidationError("duplicate task id")

    known_ids = set(task_ids)
    edge_pairs: set[tuple[str, str]] = set()
    incoming_dependencies: dict[str, set[str]] = defaultdict(set)
    for edge in workflow.edges:
        if edge.source_task_id not in known_ids:
            raise GraphValidationError(f"unknown source task: {edge.source_task_id}")
        if edge.target_task_id not in known_ids:
            raise GraphValidationError(f"unknown target task: {edge.target_task_id}")
        if edge.source_task_id == edge.target_task_id:
            raise GraphValidationError("self dependency")
        pair = (edge.source_task_id, edge.target_task_id)
        if pair in edge_pairs:
            raise GraphValidationError("duplicate edge")
        edge_pairs.add(pair)
        incoming_dependencies[edge.target_task_id].add(edge.source_task_id)

    for task in workflow.tasks:
        if set(task.dependencies) != incoming_dependencies[task.id]:
            raise GraphValidationError(f"dependency mismatch for task: {task.id}")

    _kahn_order(workflow, known_ids, edge_pairs)


def _kahn_order(
    workflow: WorkflowDefinition,
    task_ids: set[str],
    edge_pairs: set[tuple[str, str]],
) -> list[str]:
    indegree = {task_id: 0 for task_id in task_ids}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for source, target in edge_pairs:
        indegree[target] += 1
        outgoing[source].append(target)

    available = sorted(task_id for task_id, degree in indegree.items() if degree == 0)
    order: list[str] = []
    while available:
        current = available.pop(0)
        order.append(current)
        for target in sorted(outgoing[current]):
            indegree[target] -= 1
            if indegree[target] == 0:
                available.append(target)
        available.sort()

    if len(order) != len(workflow.tasks):
        raise GraphValidationError("cycle detected")
    return order


def topological_order(workflow: WorkflowDefinition) -> list[str]:
    validate_workflow(workflow)
    return _kahn_order(
        workflow,
        {task.id for task in workflow.tasks},
        {(edge.source_task_id, edge.target_task_id) for edge in workflow.edges},
    )


def dependency_map(workflow: WorkflowDefinition) -> dict[str, set[str]]:
    validate_workflow(workflow)
    result = {task.id: set(task.dependencies) for task in workflow.tasks}
    return {task_id: dependencies.copy() for task_id, dependencies in result.items()}

