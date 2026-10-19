"""Safe continuation of a successful task's Codex thread."""

from collections.abc import Mapping
from dataclasses import dataclass

from codex_flow.codex_adapter.interface import CodexAdapter
from codex_flow.codex_adapter.models import CodexThreadRef, CodexTurnRef
from codex_flow.domain.models import ExecutionMode, TaskDefinition
from codex_flow.domain.status import TaskStatus


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


class ThreadContinuation:
    """Validate frozen continuation preconditions before resuming a thread."""

    def __init__(self, adapter: CodexAdapter) -> None:
        self._adapter = adapter

    async def continue_task(
        self, task: TaskDefinition, sources: Mapping[str, ContinuationSource]
    ) -> ContinuationResult:
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

        thread = await self._adapter.resume_thread(CodexThreadRef(thread_id=source.thread_id))
        turn = await self._adapter.start_turn(thread, task.prompt)
        return ContinuationResult(thread=thread, turn=turn)
