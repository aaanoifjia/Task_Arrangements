from codex_flow.codex_adapter.fake import FakeCodexAdapter, FakeScenario
from codex_flow.codex_adapter.models import EventType
from codex_flow.domain.models import (
    Edge,
    ExecutionMode,
    RetryPolicy,
    TaskDefinition,
    WorkflowDefinition,
)
from codex_flow.domain.status import TaskStatus
from codex_flow.scheduler.engine import AsyncScheduler


class SequenceAdapter(FakeCodexAdapter):
    def __init__(self, terminal_events: list[EventType]) -> None:
        super().__init__(FakeScenario.SUCCESS)
        self._terminal_events = iter(terminal_events)

    def _terminal_event(self, turn_id: str) -> EventType:
        return next(self._terminal_events)


def task(
    task_id: str,
    dependencies: list[str] | None = None,
    *,
    mode: ExecutionMode = ExecutionMode.NEW_THREAD,
    retry_attempts: int = 1,
) -> TaskDefinition:
    return TaskDefinition(
        id=task_id,
        name=task_id,
        prompt=task_id,
        cwd=".",
        dependencies=dependencies or [],
        execution_mode=mode,
        continue_from_task_id="A" if mode is ExecutionMode.CONTINUE_THREAD else None,
        retry_policy=RetryPolicy(max_attempts=retry_attempts),
    )


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


async def test_pause_prevents_start_and_resume_runs_ready_task() -> None:
    adapter = FakeCodexAdapter()
    scheduler = AsyncScheduler(workflow(task("A")), adapter)

    scheduler.actions.pause_workflow()
    assert await scheduler.run_until_idle() == {"A": TaskStatus.READY}
    assert adapter.calls == []

    scheduler.actions.resume_workflow()
    assert await scheduler.run_until_idle() == {"A": TaskStatus.SUCCESS}
    assert adapter.calls == ["create_thread", "start_turn", "stream_turn"]


async def test_retry_parent_success_releases_child() -> None:
    adapter = SequenceAdapter([EventType.TURN_FAILED, EventType.TURN_COMPLETED, EventType.TURN_COMPLETED])
    scheduler = AsyncScheduler(workflow(task("A", retry_attempts=2), task("B", ["A"])), adapter)

    assert await scheduler.run_until_idle() == {"A": TaskStatus.FAILED, "B": TaskStatus.BLOCKED}
    scheduler.actions.retry("A")

    assert await scheduler.run_until_idle() == {"A": TaskStatus.SUCCESS, "B": TaskStatus.SUCCESS}


async def test_skip_does_not_release_dependent() -> None:
    adapter = FakeCodexAdapter()
    scheduler = AsyncScheduler(
        workflow(task("A"), task("B", ["A"])),
        adapter,
        statuses={"A": TaskStatus.READY, "B": TaskStatus.PENDING},
    )

    scheduler.actions.skip("A")

    assert await scheduler.run_until_idle() == {"A": TaskStatus.SKIPPED, "B": TaskStatus.BLOCKED}
    assert adapter.calls == []


async def test_mark_success_releases_dependent() -> None:
    adapter = FakeCodexAdapter()
    scheduler = AsyncScheduler(
        workflow(task("A"), task("B", ["A"])),
        adapter,
        statuses={"A": TaskStatus.READY, "B": TaskStatus.PENDING},
    )

    scheduler.actions.mark_success("A")

    assert await scheduler.run_until_idle() == {"A": TaskStatus.SUCCESS, "B": TaskStatus.SUCCESS}
    assert adapter.calls == ["create_thread", "start_turn", "stream_turn"]


async def test_continue_thread_resumes_and_reuses_source_thread() -> None:
    adapter = FakeCodexAdapter()
    scheduler = AsyncScheduler(
        workflow(task("A"), task("B", ["A"], mode=ExecutionMode.CONTINUE_THREAD)), adapter
    )

    assert await scheduler.run_until_idle() == {"A": TaskStatus.SUCCESS, "B": TaskStatus.SUCCESS}
    assert scheduler.thread_ids == {"A": "fake-thread-1", "B": "fake-thread-1"}
    assert scheduler.turn_ids == {"A": "fake-turn-1", "B": "fake-turn-2"}
    assert adapter.calls == [
        "create_thread",
        "start_turn",
        "stream_turn",
        "resume_thread",
        "start_turn",
        "stream_turn",
    ]


async def test_new_thread_behavior_creates_distinct_threads() -> None:
    adapter = FakeCodexAdapter()
    scheduler = AsyncScheduler(workflow(task("A"), task("B")), adapter)

    assert await scheduler.run_until_idle() == {"A": TaskStatus.SUCCESS, "B": TaskStatus.SUCCESS}
    assert scheduler.thread_ids == {"A": "fake-thread-1", "B": "fake-thread-2"}
