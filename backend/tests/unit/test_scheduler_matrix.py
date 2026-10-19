import asyncio

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter, FakeScenario
from codex_flow.codex_adapter.models import CodexEvent, CodexTurnRef, EventType
from codex_flow.domain.models import (
    Edge,
    ExecutionMode,
    RetryPolicy,
    TaskDefinition,
    WorkflowDefinition,
)
from codex_flow.domain.status import TaskStatus
from codex_flow.scheduler.engine import AsyncScheduler
from codex_flow.scheduler.graph import GraphValidationError


class SequenceAdapter(FakeCodexAdapter):
    def __init__(self, events: list[EventType]) -> None:
        super().__init__()
        self._events = iter(events)

    def _terminal_event(self, turn_id: str) -> EventType:
        return next(self._events)


class ParallelAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.active = 0
        self.peak = 0

    async def stream_turn(self, turn: CodexTurnRef):  # type: ignore[override]
        self.calls.append("stream_turn")
        self.active += 1
        self.peak = max(self.peak, self.active)
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        await asyncio.sleep(0)
        self.active -= 1
        yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)


def task(
    task_id: str,
    dependencies: list[str] | None = None,
    *,
    cwd: str = ".",
    mode: ExecutionMode = ExecutionMode.NEW_THREAD,
    retry_attempts: int = 1,
) -> TaskDefinition:
    return TaskDefinition(
        id=task_id,
        name=task_id,
        prompt=task_id,
        cwd=cwd,
        dependencies=dependencies or [],
        execution_mode=mode,
        continue_from_task_id="A" if mode is ExecutionMode.CONTINUE_THREAD else None,
        retry_policy=RetryPolicy(max_attempts=retry_attempts),
    )


def workflow(*tasks: TaskDefinition) -> WorkflowDefinition:
    return WorkflowDefinition(
        id="matrix",
        name="Matrix",
        tasks=list(tasks),
        edges=[
            Edge(source_task_id=dependency, target_task_id=item.id)
            for item in tasks
            for dependency in item.dependencies
        ],
    )


@pytest.mark.parametrize(
    ("tasks", "expected"),
    [
        ((task("A"),), {"A": TaskStatus.SUCCESS}),
        ((task("A"), task("B", ["A"])), {"A": TaskStatus.SUCCESS, "B": TaskStatus.SUCCESS}),
        ((task("A"), task("B", ["A"]), task("C", ["A"])), {"A": TaskStatus.SUCCESS, "B": TaskStatus.SUCCESS, "C": TaskStatus.SUCCESS}),
        ((task("B"), task("C"), task("D", ["B", "C"])), {"B": TaskStatus.SUCCESS, "C": TaskStatus.SUCCESS, "D": TaskStatus.SUCCESS}),
    ],
)
async def test_dependency_matrix(tasks: tuple[TaskDefinition, ...], expected: dict[str, TaskStatus]) -> None:
    assert await AsyncScheduler(workflow(*tasks), FakeCodexAdapter()).run_until_idle() == expected


@pytest.mark.parametrize("scenario", [FakeScenario.FAILED, FakeScenario.INTERRUPTED])
async def test_failure_or_interrupt_blocks_children(scenario: FakeScenario) -> None:
    result = await AsyncScheduler(workflow(task("A"), task("B", ["A"])), FakeCodexAdapter(scenario)).run_until_idle()
    assert result["B"] is TaskStatus.BLOCKED


async def test_retry_then_success_releases_child() -> None:
    scheduler = AsyncScheduler(
        workflow(task("A", retry_attempts=2), task("B", ["A"])),
        SequenceAdapter([EventType.TURN_FAILED, EventType.TURN_COMPLETED, EventType.TURN_COMPLETED]),
    )
    await scheduler.run_until_idle()
    scheduler.actions.retry("A")
    assert (await scheduler.run_until_idle())["B"] is TaskStatus.SUCCESS


async def test_skip_blocks_but_mark_success_releases_child() -> None:
    skipped = AsyncScheduler(workflow(task("A"), task("B", ["A"])), FakeCodexAdapter(), statuses={"A": TaskStatus.READY, "B": TaskStatus.PENDING})
    skipped.actions.skip("A")
    assert (await skipped.run_until_idle())["B"] is TaskStatus.BLOCKED

    successful = AsyncScheduler(workflow(task("A"), task("B", ["A"])), FakeCodexAdapter(), statuses={"A": TaskStatus.READY, "B": TaskStatus.PENDING})
    successful.actions.mark_success("A")
    assert (await successful.run_until_idle())["B"] is TaskStatus.SUCCESS


async def test_pause_resume_and_continue_thread() -> None:
    scheduler = AsyncScheduler(
        workflow(task("A"), task("B", ["A"], mode=ExecutionMode.CONTINUE_THREAD)), FakeCodexAdapter()
    )
    scheduler.actions.pause_workflow()
    assert (await scheduler.run_until_idle())["A"] is TaskStatus.READY
    scheduler.actions.resume_workflow()
    assert (await scheduler.run_until_idle())["B"] is TaskStatus.SUCCESS
    assert scheduler.thread_ids["A"] == scheduler.thread_ids["B"]


@pytest.mark.parametrize(("limit", "expected_peak"), [(1, 1), (2, 2)])
async def test_global_concurrency_limit(limit: int, expected_peak: int) -> None:
    adapter = ParallelAdapter()
    await AsyncScheduler(workflow(task("A", cwd="one"), task("B", cwd="two")), adapter, max_concurrency=limit).run_until_idle()
    assert adapter.peak == expected_peak


async def test_workspace_write_locks_serialize_same_cwd_but_not_different_cwds() -> None:
    same = ParallelAdapter()
    await AsyncScheduler(workflow(task("A", cwd="shared"), task("B", cwd="shared")), same, max_concurrency=2).run_until_idle()
    assert same.peak == 1

    different = ParallelAdapter()
    await AsyncScheduler(workflow(task("A", cwd="one"), task("B", cwd="two")), different, max_concurrency=2).run_until_idle()
    assert different.peak == 2


def test_cycle_is_rejected() -> None:
    with pytest.raises(GraphValidationError, match="cycle"):
        AsyncScheduler(workflow(task("A", ["B"]), task("B", ["A"])), FakeCodexAdapter())
