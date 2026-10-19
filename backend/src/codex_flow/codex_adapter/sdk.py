"""Official-SDK implementation of the internal Codex adapter."""

from collections.abc import AsyncIterator
from typing import Any

from openai_codex import ApprovalMode, AsyncCodex, Sandbox

from codex_flow.codex_adapter.models import (
    CodexEvent, CodexExecutionConfig, CodexThreadRef, CodexThreadSnapshot,
    CodexTurnOutcome, CodexTurnRef, EventType,
)
from codex_flow.domain.models import SandboxMode


class SdkCodexAdapter:
    def __init__(self) -> None:
        self._codex = AsyncCodex()
        self._threads: dict[str, Any] = {}
        self._turns: dict[str, Any] = {}

    async def create_thread(self, config: CodexExecutionConfig) -> CodexThreadRef:
        thread = await self._codex.thread_start(
            cwd=config.cwd, model=config.model, approval_mode=ApprovalMode.auto_review,
            sandbox=self._sandbox(config.sandbox),
        )
        self._threads[thread.id] = thread
        return CodexThreadRef(thread_id=thread.id)

    async def resume_thread(self, thread: CodexThreadRef) -> CodexThreadRef:
        resumed = await self._codex.thread_resume(thread.thread_id)
        self._threads[resumed.id] = resumed
        return CodexThreadRef(thread_id=resumed.id)

    async def start_turn(self, thread: CodexThreadRef, prompt: str) -> CodexTurnRef:
        handle = self._threads[thread.thread_id]
        turn = await handle.turn(prompt, approval_mode=ApprovalMode.auto_review)
        self._turns[turn.id] = turn
        return CodexTurnRef(thread_id=thread.thread_id, turn_id=turn.id)

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        handle = self._turns[turn.turn_id]
        async for notification in handle.stream():
            method = str(notification.method)
            payload = notification.payload
            event_type = self._event_type(method, payload)
            message = getattr(payload, "delta", None)
            yield CodexEvent(event_type=event_type, thread_id=turn.thread_id, turn_id=turn.turn_id,
                             message=message if isinstance(message, str) else None)

    async def interrupt_turn(self, turn: CodexTurnRef) -> CodexTurnOutcome:
        handle = self._turns[turn.turn_id]
        await handle.interrupt()
        return CodexTurnOutcome(thread_id=turn.thread_id, turn_id=turn.turn_id,
                                terminal_event=EventType.TURN_INTERRUPTED)

    async def read_thread(self, thread: CodexThreadRef) -> CodexThreadSnapshot:
        handle = self._threads.get(thread.thread_id)
        if handle is not None:
            await handle.read()
        return CodexThreadSnapshot(thread=thread)

    async def set_thread_name(self, thread: CodexThreadRef, name: str) -> None:
        handle = self._threads[thread.thread_id]
        await handle.set_name(name)

    async def close(self) -> None:
        await self._codex.close()

    @staticmethod
    def _sandbox(mode: SandboxMode) -> Sandbox:
        return {SandboxMode.WORKSPACE_WRITE: Sandbox.workspace_write,
                SandboxMode.READ_ONLY: Sandbox.read_only,
                SandboxMode.FULL_ACCESS: Sandbox.full_access}[mode]

    @staticmethod
    def _event_type(method: str, payload: object) -> EventType:
        if method == "turn/started":
            return EventType.TURN_STARTED
        if method == "turn/completed":
            status = getattr(getattr(payload, "turn", payload), "status", None)
            value = getattr(status, "value", status)
            if value == "interrupted": return EventType.TURN_INTERRUPTED
            if value == "failed": return EventType.TURN_FAILED
            return EventType.TURN_COMPLETED
        if method == "item/agentMessage/delta": return EventType.AGENT_MESSAGE
        if method == "item/started": return EventType.TOOL_STARTED
        if method == "item/completed": return EventType.TOOL_COMPLETED
        return EventType.TRANSPORT_ERROR
