import pytest

from codex_flow.application.workflow_transfer import (
    parse_workflow_definition_export,
    serialize_workflow_definition,
)
from codex_flow.domain.models import Edge, ExecutionMode, TaskDefinition, WorkflowDefinition


def task(
    task_id: str,
    *,
    dependencies: list[str] | None = None,
    execution_mode: ExecutionMode = ExecutionMode.NEW_THREAD,
    continue_from_task_id: str | None = None,
) -> TaskDefinition:
    return TaskDefinition(
        id=task_id,
        name=f"节点 {task_id}",
        prompt=f"  保留的提示 {task_id}  \n下一行\t终止  ",
        cwd=".",
        dependencies=dependencies or [],
        execution_mode=execution_mode,
        continue_from_task_id=continue_from_task_id,
    )


@pytest.mark.parametrize(
    "workflow",
    [
        WorkflowDefinition(
            id="linear-unicode",
            name="线性流程",
            description="  保留描述  ",
            tasks=[task("A"), task("B", dependencies=["A"])],
            edges=[Edge(source_task_id="A", target_task_id="B")],
        ),
        WorkflowDefinition(
            id="fork-join-unicode",
            name="分叉汇合",
            tasks=[task("A"), task("B", dependencies=["A"]), task("C", dependencies=["A"]), task("D", dependencies=["B", "C"])],
            edges=[
                Edge(source_task_id="A", target_task_id="B"),
                Edge(source_task_id="A", target_task_id="C"),
                Edge(source_task_id="B", target_task_id="D"),
                Edge(source_task_id="C", target_task_id="D"),
            ],
        ),
        WorkflowDefinition(
            id="continuation-unicode",
            name="继续线程",
            tasks=[task("A"), task("B", dependencies=["A"], execution_mode=ExecutionMode.CONTINUE_THREAD, continue_from_task_id="A")],
            edges=[Edge(source_task_id="A", target_task_id="B")],
        ),
    ],
    ids=["linear", "fork_join", "continuation"],
)
def test_workflow_definitions_round_trip_without_prompt_or_whitespace_loss(
    workflow: WorkflowDefinition,
) -> None:
    restored = parse_workflow_definition_export(serialize_workflow_definition(workflow))

    assert restored == workflow
    assert [task.prompt for task in restored.tasks] == [task.prompt for task in workflow.tasks]
