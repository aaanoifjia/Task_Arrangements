import pytest

from codex_flow.domain.models import Edge, ExecutionMode, TaskDefinition, WorkflowDefinition
from codex_flow.scheduler.graph import GraphValidationError, dependency_map, topological_order


def task(task_id: str, dependencies: list[str] | None = None, **kwargs: object) -> TaskDefinition:
    return TaskDefinition(id=task_id, name=task_id, prompt="run", cwd=".", dependencies=dependencies or [], **kwargs)


def workflow(tasks: list[TaskDefinition], edges: list[tuple[str, str]]) -> WorkflowDefinition:
    return WorkflowDefinition(id="wf", name="workflow", tasks=tasks, edges=[Edge(source_task_id=s, target_task_id=t) for s, t in edges])


def test_thread_modes() -> None:
    assert task("A").execution_mode is ExecutionMode.NEW_THREAD
    continued = task("B", execution_mode=ExecutionMode.CONTINUE_THREAD, continue_from_task_id="A")
    assert continued.continue_from_task_id == "A"


@pytest.mark.parametrize("kwargs, message", [
    ({"execution_mode": ExecutionMode.CONTINUE_THREAD}, "continue_from_task_id is required"),
    ({"continue_from_task_id": "A"}, "continue_from_task_id must be None"),
])
def test_invalid_thread_modes(kwargs: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        task("A", **kwargs)


@pytest.mark.parametrize(
    ("tasks", "edges", "message"),
    [
        ([task("A"), task("A")], [], "duplicate task id"),
        ([task("A")], [("X", "A")], "unknown source task"),
        ([task("A")], [("A", "X")], "unknown target task"),
        ([task("A")], [("A", "A")], "self dependency"),
        ([task("A"), task("B", ["A"])], [("A", "B"), ("A", "B")], "duplicate edge"),
        ([task("A"), task("B")], [("A", "B")], "dependency mismatch"),
        ([task("A", ["C"]), task("B", ["A"]), task("C", ["B"])], [("A", "B"), ("B", "C"), ("C", "A")], "cycle detected"),
    ],
)
def test_graph_validation_rejects(tasks: list[TaskDefinition], edges: list[tuple[str, str]], message: str) -> None:
    with pytest.raises(GraphValidationError, match=message):
        topological_order(workflow(tasks, edges))


def test_topological_orders() -> None:
    assert topological_order(workflow([task("A")], [])) == ["A"]
    assert topological_order(workflow([task("A"), task("B", ["A"]), task("C", ["B"])], [("A", "B"), ("B", "C")])) == ["A", "B", "C"]
    assert topological_order(workflow([task("A"), task("B", ["A"]), task("C", ["A"])], [("A", "B"), ("A", "C")])) == ["A", "B", "C"]
    assert topological_order(workflow([task("root"), task("z", ["root"]), task("a", ["root"])], [("root", "z"), ("root", "a")])) == ["root", "a", "z"]


def test_dependency_map() -> None:
    result = dependency_map(workflow([task("A"), task("B", ["A"])], [("A", "B")]))
    assert result == {"A": set(), "B": {"A"}}
    result["B"].add("C")
    assert dependency_map(workflow([task("A"), task("B", ["A"])], [("A", "B")]))["B"] == {"A"}
