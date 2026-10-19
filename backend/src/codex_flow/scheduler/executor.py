"""Adapter-backed execution of one scheduled task."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import cast

from codex_flow.codex_adapter.interface import CodexAdapter
from codex_flow.codex_adapter.models import (
    CodexEvent,
    CodexExecutionConfig,
    CodexTurnRef,
    EventType,
)
from codex_flow.domain.models import SandboxMode, TaskDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.scheduler.locks import (
    GlobalConcurrencyLimiter,
    ThreadTurnLockManager,
    WorkspaceLockManager,
)


@dataclass(frozen=True)
class ExecutionResult:
    """The state observed while executing one adapter turn."""

    started: bool
    status: TaskStatus


def command_completion_failed(event: CodexEvent) -> bool:
    """Classify an explicit command completion conservatively and deterministically."""
    if event.event_type is not EventType.TOOL_COMPLETED:
        return False
    item_type = event.details.get("item_type")
    if not isinstance(item_type, str) or "command" not in item_type.casefold():
        return False
    status = event.details.get("status")
    failed_status = isinstance(status, str) and status.casefold() in {"failed", "declined"}
    exit_code = event.details.get("exit_code")
    failed_exit_code = isinstance(exit_code, int) and not isinstance(exit_code, bool) and exit_code != 0
    return failed_status or failed_exit_code


class TaskExecutor:
    """Run a task while applying the scheduler's capacity and lock rules."""

    def __init__(
        self,
        adapter: CodexAdapter,
        limiter: GlobalConcurrencyLimiter,
        workspace_locks: WorkspaceLockManager,
        thread_locks: ThreadTurnLockManager,
    ) -> None:
        self._adapter = adapter
        self._limiter = limiter
        self._workspace_locks = workspace_locks
        self._thread_locks = thread_locks

    async def execute(self, task: TaskDefinition) -> ExecutionResult:
        """Create a thread, start a turn, and fail closed on incomplete streams."""
        async with self._limiter.slot():
            if task.sandbox is SandboxMode.READ_ONLY:
                return await self._execute_turn(task)
            async with self._workspace_locks.acquire_write(task.cwd):
                return await self._execute_turn(task)

    async def _execute_turn(self, task: TaskDefinition) -> ExecutionResult:
        config = CodexExecutionConfig(
            cwd=task.cwd,
            sandbox=task.sandbox,
            model=task.model,
            reasoning_effort=task.reasoning_effort,
            approval_mode=task.approval_mode,
        )
        try:
            thread = await self._adapter.create_thread(config)
            async with self._thread_locks.acquire_turn(thread.thread_id):
                turn = await self._adapter.start_turn(thread, task.prompt)
                return await self._stream_terminal(turn)
        except Exception:  # noqa: BLE001 - an adapter transport failure must fail closed.
            return ExecutionResult(started=False, status=TaskStatus.FAILED)

    async def _stream_terminal(self, turn: CodexTurnRef) -> ExecutionResult:
        """Map the adapter's terminal events into frozen scheduler statuses."""
        started = False
        failed_command_observed = False
        stream = cast("AsyncIterator[CodexEvent]", self._adapter.stream_turn(turn))
        async for event in stream:
            if event.event_type is EventType.TURN_STARTED:
                started = True
            elif command_completion_failed(event):
                failed_command_observed = True
            elif event.event_type is EventType.TURN_COMPLETED:
                status = TaskStatus.FAILED if failed_command_observed else TaskStatus.SUCCESS
                return ExecutionResult(started=started, status=status)
            elif event.event_type in {EventType.TURN_FAILED, EventType.TRANSPORT_ERROR}:
                return ExecutionResult(started=started, status=TaskStatus.FAILED)
            elif event.event_type is EventType.TURN_INTERRUPTED:
                return ExecutionResult(started=started, status=TaskStatus.INTERRUPTED)
            elif event.event_type is EventType.ATTENTION_REQUIRED:
                return ExecutionResult(started=started, status=TaskStatus.NEEDS_ATTENTION)
        return ExecutionResult(started=started, status=TaskStatus.FAILED)
