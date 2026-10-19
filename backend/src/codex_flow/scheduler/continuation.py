"""Safe continuation of a successful task's Codex thread."""

from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from typing import cast

from codex_flow.codex_adapter.interface import CodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexThreadRef, CodexTurnRef, EventType
from codex_flow.domain.models import ExecutionMode, SandboxMode, TaskDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.scheduler.locks import (
    GlobalConcurrencyLimiter,
    ThreadTurnLockManager,
    WorkspaceLockManager,
)


class ContinuationError(ValueError):
    """Raised when an existing thread cannot safely be continued."""


@dataclass(frozen=True)
class ContinuationSource:
    task_id: str
    status: TaskStatus
    thread_id: str | None
    has_active_turn: bool


@dataclass(frozen=True)
class ContinuationResult:
    thread: CodexThreadRef
    turn: CodexTurnRef


@dataclass(frozen=True)
class ContinuationExecutionResult:
    thread: CodexThreadRef
    turn: CodexTurnRef
    started: bool
    status: TaskStatus


class ThreadContinuation:
    """Validate frozen continuation preconditions before resuming a thread."""

    def __init__(self, adapter: CodexAdapter) -> None:
        self._adapter = adapter

    async def continue_task(
        self, task: TaskDefinition, sources: Mapping[str, ContinuationSource]
    ) -> ContinuationResult:
        thread = await self._resume_thread(task, sources)
        turn = await self._adapter.start_turn(thread, task.prompt)
        return ContinuationResult(thread=thread, turn=turn)

    async def _resume_thread(
        self, task: TaskDefinition, sources: Mapping[str, ContinuationSource]
    ) -> CodexThreadRef:
        if task.execution_mode is not ExecutionMode.CONTINUE_THREAD:
            raise ContinuationError("task execution mode must be CONTINUE_THREAD")
        source_id = task.continue_from_task_id
        if source_id is None:
            raise ContinuationError("continue_from_task_id is required")
        try:
            source = sources[source_id]
        except KeyError as error:
            raise ContinuationError(f"continuation source does not exist: {source_id}") from error
        if source.status is not TaskStatus.SUCCESS:
            raise ContinuationError("continuation source must be SUCCESS")
        if source.thread_id is None:
            raise ContinuationError("continuation source has no thread_id")
        if source.has_active_turn:
            raise ContinuationError("continuation source has an active turn")

        return await self._adapter.resume_thread(CodexThreadRef(thread_id=source.thread_id))

    async def execute_task(
        self,
        task: TaskDefinition,
        sources: Mapping[str, ContinuationSource],
        limiter: GlobalConcurrencyLimiter,
        workspace_locks: WorkspaceLockManager,
        thread_locks: ThreadTurnLockManager,
    ) -> ContinuationExecutionResult:
        """Resume and stream a new turn under the same lock rules as new threads."""
        async with limiter.slot():
            if task.sandbox is SandboxMode.READ_ONLY:
                return await self._execute_turn(task, sources, thread_locks)
            async with workspace_locks.acquire_write(task.cwd):
                return await self._execute_turn(task, sources, thread_locks)

    async def _execute_turn(
        self,
        task: TaskDefinition,
        sources: Mapping[str, ContinuationSource],
        thread_locks: ThreadTurnLockManager,
    ) -> ContinuationExecutionResult:
        thread = await self._resume_thread(task, sources)
        started = False
        async with thread_locks.acquire_turn(thread.thread_id):
            turn = await self._adapter.start_turn(thread, task.prompt)
            stream = cast("AsyncIterator[CodexEvent]", self._adapter.stream_turn(turn))
            async for event in stream:
                if event.event_type is EventType.TURN_STARTED:
                    started = True
                elif event.event_type is EventType.TURN_COMPLETED:
                    return ContinuationExecutionResult(thread, turn, started, TaskStatus.SUCCESS)
                elif event.event_type in {EventType.TURN_FAILED, EventType.TRANSPORT_ERROR}:
                    return ContinuationExecutionResult(thread, turn, started, TaskStatus.FAILED)
                elif event.event_type is EventType.TURN_INTERRUPTED:
                    return ContinuationExecutionResult(thread, turn, started, TaskStatus.INTERRUPTED)
                elif event.event_type is EventType.ATTENTION_REQUIRED:
                    return ContinuationExecutionResult(
                        thread, turn, started, TaskStatus.NEEDS_ATTENTION
                    )
        return ContinuationExecutionResult(thread, turn, started, TaskStatus.FAILED)
