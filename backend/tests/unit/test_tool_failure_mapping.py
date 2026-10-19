from collections.abc import AsyncIterator
from types import SimpleNamespace

from codex_flow.codex_adapter.models import (
    CodexEvent,
    CodexExecutionConfig,
    CodexThreadRef,
    CodexThreadSnapshot,
    CodexTurnOutcome,
    CodexTurnRef,
    EventType,
)
from codex_flow.codex_adapter.sdk import SdkCodexAdapter
from codex_flow.domain.models import Edge, TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.scheduler.engine import AsyncScheduler
from codex_flow.scheduler.executor import TaskExecutor
from codex_flow.scheduler.locks import (
    GlobalConcurrencyLimiter,
    ThreadTurnLockManager,
    WorkspaceLockManager,
)


class EventAdapter:
    """Adapter double that makes stream consumption observable."""

    def __init__(self, events_by_turn: list[list[CodexEvent]]) -> None:
        self._events_by_turn = iter(events_by_turn)
        self.calls: list[str] = []
        self.stream_event_count = 0
        self._thread_count = 0
        self._turn_count = 0

    async def create_thread(self, config: CodexExecutionConfig) -> CodexThreadRef:
        del config
        self.calls.append("create_thread")
        self._thread_count += 1
        return CodexThreadRef(thread_id=f"thread-{self._thread_count}")

    async def resume_thread(self, thread: CodexThreadRef) -> CodexThreadRef:
        self.calls.append("resume_thread")
        return thread

    async def start_turn(self, thread: CodexThreadRef, prompt: str) -> CodexTurnRef:
        del prompt
        self.calls.append("start_turn")
        self._turn_count += 1
        return CodexTurnRef(thread_id=thread.thread_id, turn_id=f"turn-{self._turn_count}")

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.calls.append("stream_turn")
        for event in next(self._events_by_turn):
            self.stream_event_count += 1
            yield event.model_copy(update={"thread_id": turn.thread_id, "turn_id": turn.turn_id})

    async def interrupt_turn(self, turn: CodexTurnRef) -> CodexTurnOutcome:
        return CodexTurnOutcome(
            thread_id=turn.thread_id,
            turn_id=turn.turn_id,
            terminal_event=EventType.TURN_INTERRUPTED,
        )

    async def read_thread(self, thread: CodexThreadRef) -> CodexThreadSnapshot:
        return CodexThreadSnapshot(thread=thread)

    async def set_thread_name(self, thread: CodexThreadRef, name: str) -> None:
        del thread, name

    async def close(self) -> None:
        return None


def event(event_type: EventType, **details: object) -> CodexEvent:
    return CodexEvent(event_type=event_type, thread_id="placeholder", details=details)


def command(status: str | None = None, exit_code: int | None = None) -> CodexEvent:
    details: dict[str, object] = {"item_type": "commandExecution"}
    if status is not None:
        details["status"] = status
    if exit_code is not None:
        details["exit_code"] = exit_code
    return event(EventType.TOOL_COMPLETED, **details)


def task(task_id: str, dependencies: list[str] | None = None) -> TaskDefinition:
    return TaskDefinition(
        id=task_id,
        name=task_id,
        prompt=task_id,
        cwd=".",
        dependencies=dependencies or [],
    )


async def run_executor(events: list[CodexEvent]) -> tuple[TaskStatus, EventAdapter]:
    adapter = EventAdapter([events])
    executor = TaskExecutor(
        adapter,
        GlobalConcurrencyLimiter(1),
        WorkspaceLockManager(),
        ThreadTurnLockManager(),
    )
    result = await executor.execute(task("A"))
    return result.status, adapter


async def test_successful_command_completion_allows_turn_success() -> None:
    status, _ = await run_executor(
        [event(EventType.TURN_STARTED), command(status="completed", exit_code=0), event(EventType.TURN_COMPLETED)]
    )

    assert status is TaskStatus.SUCCESS


async def test_failed_command_completion_maps_completed_turn_to_failed() -> None:
    status, adapter = await run_executor(
        [event(EventType.TURN_STARTED), command(status="failed", exit_code=1), event(EventType.TURN_COMPLETED)]
    )

    assert status is TaskStatus.FAILED
    assert adapter.stream_event_count == 3


async def test_declined_command_completion_maps_completed_turn_to_failed() -> None:
    status, _ = await run_executor(
        [event(EventType.TURN_STARTED), command(status="declined"), event(EventType.TURN_COMPLETED)]
    )

    assert status is TaskStatus.FAILED


async def test_failed_command_then_failed_turn_is_failed() -> None:
    status, _ = await run_executor(
        [event(EventType.TURN_STARTED), command(status="failed", exit_code=1), event(EventType.TURN_FAILED)]
    )

    assert status is TaskStatus.FAILED


async def test_parent_command_failure_blocks_dependent_child_thread_creation() -> None:
    adapter = EventAdapter(
        [[event(EventType.TURN_STARTED), command(status="failed", exit_code=1), event(EventType.TURN_COMPLETED)]]
    )
    workflow = WorkflowDefinition(
        id="failure-blocking",
        name="Failure blocking",
        tasks=[task("parent"), task("child", ["parent"])],
        edges=[Edge(source_task_id="parent", target_task_id="child")],
    )
    scheduler = AsyncScheduler(workflow, adapter)

    assert await scheduler.run_until_idle() == {
        "parent": TaskStatus.FAILED,
        "child": TaskStatus.BLOCKED,
    }
    assert adapter.calls.count("create_thread") == 1


def test_sdk_command_completion_details_are_stable_builtin_values() -> None:
    item = SimpleNamespace(
        type=SimpleNamespace(value="commandExecution"),
        id="item-1",
        status=SimpleNamespace(value="failed"),
        exit_code=1,
        command="exit 1",
    )

    assert SdkCodexAdapter._event_details("item/completed", SimpleNamespace(item=item)) == {
        "item_type": "commandExecution",
        "item_id": "item-1",
        "status": "failed",
        "exit_code": 1,
        "command": "exit 1",
    }
