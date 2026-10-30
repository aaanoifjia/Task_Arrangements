"""The scheduler-visible asynchronous Codex integration contract."""

from collections.abc import AsyncIterator
from typing import Protocol

from codex_flow.codex_adapter.models import (
    CodexEvent,
    CodexExecutionConfig,
    CodexThreadRef,
    CodexThreadSnapshot,
    CodexTurnOutcome,
    CodexTurnRef,
)


class CodexStartupError(RuntimeError):
    """A deterministic failure before a thread reference is created."""


class CodexAdapter(Protocol):
    async def create_thread(self, config: CodexExecutionConfig) -> CodexThreadRef: ...

    async def resume_thread(self, thread: CodexThreadRef) -> CodexThreadRef: ...

    async def start_turn(self, thread: CodexThreadRef, prompt: str) -> CodexTurnRef: ...

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]: ...

    async def interrupt_turn(self, turn: CodexTurnRef) -> CodexTurnOutcome: ...

    async def read_thread(self, thread: CodexThreadRef) -> CodexThreadSnapshot: ...

    async def set_thread_name(self, thread: CodexThreadRef, name: str) -> None: ...

    async def close(self) -> None: ...
