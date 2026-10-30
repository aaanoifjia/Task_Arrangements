"""Official-SDK implementation of the internal Codex adapter."""

import os
from collections.abc import AsyncIterator, Mapping
from typing import Any

from openai_codex import ApprovalMode, AsyncCodex, Sandbox, TransportClosedError
from openai_codex.client import CodexConfig

from codex_flow.codex_adapter.interface import CodexStartupError
from codex_flow.codex_adapter.models import (
    CodexEvent,
    CodexExecutionConfig,
    CodexThreadRef,
    CodexThreadSnapshot,
    CodexTurnOutcome,
    CodexTurnRef,
    EventType,
)
from codex_flow.domain.models import SandboxMode


class SdkCodexAdapter:
    def __init__(self) -> None:
        self._codex = AsyncCodex(CodexConfig(env=_codex_environment()))
        self._threads: dict[str, Any] = {}
        self._turns: dict[str, Any] = {}

    async def create_thread(self, config: CodexExecutionConfig) -> CodexThreadRef:
        try:
            thread = await self._codex.thread_start(
                cwd=config.cwd, model=config.model, approval_mode=ApprovalMode.auto_review,
                sandbox=self._sandbox(config.sandbox),
            )
        except TransportClosedError as error:
            raise CodexStartupError("Codex closed before creating a thread") from error
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
            if event_type is None:
                continue
            message = getattr(payload, "delta", None)
            yield CodexEvent(
                event_type=event_type,
                thread_id=turn.thread_id,
                turn_id=turn.turn_id,
                message=message if isinstance(message, str) else None,
                details=self._event_details(method, payload),
            )

    async def interrupt_turn(self, turn: CodexTurnRef) -> CodexTurnOutcome:
        handle = self._turns[turn.turn_id]
        await handle.interrupt()
        return CodexTurnOutcome(thread_id=turn.thread_id, turn_id=turn.turn_id,
                                terminal_event=EventType.TURN_INTERRUPTED)

    async def read_thread(self, thread: CodexThreadRef) -> CodexThreadSnapshot:
        handle = self._threads.get(thread.thread_id)
        if handle is None:
            handle = await self._codex.thread_resume(thread.thread_id)
            self._threads[thread.thread_id] = handle
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
    def _event_type(method: str, payload: object) -> EventType | None:
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
        # The app-server emits informational notifications (for example token
        # usage and moderation metadata) during an otherwise healthy turn.
        # They are not transport failures and must not terminate the task.
        return None

    @classmethod
    def _event_details(cls, method: str, payload: object) -> dict[str, object]:
        """Keep command execution outcomes visible without leaking SDK types."""
        if method != "item/completed":
            return {}
        item = getattr(payload, "item", payload)
        item_type = cls._plain_value(getattr(item, "type", None))
        if not isinstance(item_type, str) or "command" not in item_type.casefold():
            return {}

        details: dict[str, object] = {"item_type": item_type}
        for detail_name, attribute_name in (
            ("item_id", "id"),
            ("status", "status"),
            ("exit_code", "exit_code"),
            ("command", "command"),
        ):
            value = getattr(item, attribute_name, None)
            if value is not None:
                details[detail_name] = cls._plain_value(value)
        return details

    @staticmethod
    def _plain_value(value: object) -> str | int | float | bool | None:
        """Normalize SDK enum-like values to stable built-in values."""
        raw = getattr(value, "value", value)
        if raw is None or isinstance(raw, (str, int, float, bool)):
            return raw
        return str(raw)


def _codex_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    """Preserve the Windows user home for the SDK-owned Codex subprocess.

    Codex CLI resolves its configuration home from ``HOME`` on this host even
    when Windows profile variables are present. The desktop sidecar inherits
    the user's profile variables, so derive only the missing portable alias
    without hardcoding a user or machine-specific path.
    """
    environment = dict(os.environ if source is None else source)
    if environment.get("HOME"):
        return environment
    profile = environment.get("USERPROFILE")
    if not profile:
        drive = environment.get("HOMEDRIVE")
        path = environment.get("HOMEPATH")
        if drive and path:
            profile = f"{drive}{path}"
    if profile:
        environment["HOME"] = profile
    return environment
