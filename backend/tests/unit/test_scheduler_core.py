from codex_flow.codex_adapter.fake import FakeCodexAdapter, FakeScenario
from codex_flow.domain.models import Edge, TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.scheduler.engine import AsyncScheduler


def workflow(*tasks: TaskDefinition) -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=list(tasks),
        edges=[
            Edge(source_task_id=dependency, target_task_id=item.id)
            for item in tasks
            for dependency in item.dependencies
        ],
    )


def task(task_id: str, dependencies: list[str] | None = None) -> TaskDefinition:
    return TaskDefinition(
        id=task_id,
        name=task_id,
        prompt=f"run {task_id}",
        cwd=".",
        dependencies=dependencies or [],
    )


async def test_scheduler_runs_a_dependency_chain_in_topological_order() -> None:
    adapter = FakeCodexAdapter()
    scheduler = AsyncScheduler(workflow(task("B", ["A"]), task("A")), adapter)

    statuses = await scheduler.run_until_idle()

    assert statuses == {"A": TaskStatus.SUCCESS, "B": TaskStatus.SUCCESS}
    assert adapter.calls == [
        "create_thread",
        "start_turn",
        "stream_turn",
        "create_thread",
        "start_turn",
        "stream_turn",
    ]


async def test_scheduler_fails_closed_and_blocks_children() -> None:
    adapter = FakeCodexAdapter(FakeScenario.FAILED)
    scheduler = AsyncScheduler(workflow(task("A"), task("B", ["A"])), adapter)

    statuses = await scheduler.run_until_idle()

    assert statuses == {"A": TaskStatus.FAILED, "B": TaskStatus.BLOCKED}
    assert adapter.calls == ["create_thread", "start_turn", "stream_turn"]


async def test_scheduler_records_interruption_and_blocks_children() -> None:
    adapter = FakeCodexAdapter(FakeScenario.INTERRUPTED)
    scheduler = AsyncScheduler(workflow(task("A"), task("B", ["A"])), adapter)

    statuses = await scheduler.run_until_idle()

    assert statuses == {"A": TaskStatus.INTERRUPTED, "B": TaskStatus.BLOCKED}


async def test_scheduler_selects_lexical_order_for_independent_tasks() -> None:
    adapter = FakeCodexAdapter()
    scheduler = AsyncScheduler(workflow(task("B"), task("A")), adapter)

    statuses = await scheduler.run_until_idle()

    assert statuses == {"A": TaskStatus.SUCCESS, "B": TaskStatus.SUCCESS}
    assert adapter.calls == [
        "create_thread",
        "start_turn",
        "stream_turn",
        "create_thread",
        "start_turn",
        "stream_turn",
    ]
