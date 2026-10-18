from codex_flow.domain.models import Edge, TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.scheduler.readiness import (
    ReadinessDecision,
    evaluate_task_readiness,
    ready_task_ids,
)


def task(task_id: str, dependencies: list[str] | None = None) -> TaskDefinition:
    return TaskDefinition(id=task_id, name=task_id, prompt="run", cwd=".", dependencies=dependencies or [])


def workflow(tasks: list[TaskDefinition], edges: list[tuple[str, str]]) -> WorkflowDefinition:
    return WorkflowDefinition(
        id="wf",
        name="workflow",
        tasks=tasks,
        edges=[Edge(source_task_id=s, target_task_id=t) for s, t in edges],
    )


def test_evaluate_readiness() -> None:
    assert evaluate_task_readiness([]) is ReadinessDecision.READY
    assert evaluate_task_readiness([TaskStatus.SUCCESS, TaskStatus.SUCCESS]) is ReadinessDecision.READY
    for status in TaskStatus:
        if status is not TaskStatus.SUCCESS:
            assert evaluate_task_readiness([status]) is ReadinessDecision.BLOCKED


def test_successful_predecessor_releases_task() -> None:
    wf = workflow([task("A"), task("B", ["A"])], [("A", "B")])
    assert ready_task_ids(wf, {"A": TaskStatus.SUCCESS, "B": TaskStatus.PENDING}) == ["B"]


def test_failed_predecessor_blocks_task() -> None:
    wf = workflow([task("A"), task("B", ["A"])], [("A", "B")])
    assert ready_task_ids(wf, {"A": TaskStatus.FAILED, "B": TaskStatus.PENDING}) == []


def test_deterministic_order_and_multiple_dependencies() -> None:
    wf = workflow(
        [task("A"), task("B", ["A"]), task("C", ["A"]), task("D", ["B", "C"])],
        [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")],
    )
    statuses = {"A": TaskStatus.SUCCESS, "B": TaskStatus.PENDING, "C": TaskStatus.PENDING, "D": TaskStatus.PENDING}
    before = statuses.copy()
    assert ready_task_ids(wf, statuses) == ["B", "C"]
    assert statuses == before
    statuses["B"] = TaskStatus.SUCCESS
    assert ready_task_ids(wf, statuses) == ["C"]
    statuses["C"] = TaskStatus.SUCCESS
    assert ready_task_ids(wf, statuses) == ["D"]


def test_missing_status_errors_and_extra_is_ignored() -> None:
    wf = workflow([task("A")], [])
    assert ready_task_ids(wf, {"A": TaskStatus.PENDING, "extra": TaskStatus.RUNNING}) == ["A"]
    try:
        ready_task_ids(wf, {})
    except ValueError as error:
        assert "missing task status" in str(error)
    else:
        raise AssertionError("expected missing status error")
