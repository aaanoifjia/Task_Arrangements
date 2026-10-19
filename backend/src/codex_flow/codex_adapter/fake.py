"""Deterministic, offline implementation of the internal Codex adapter."""

from collections.abc import AsyncIterator
from enum import StrEnum

from codex_flow.codex_adapter.models import (
    CodexEvent, CodexExecutionConfig, CodexThreadRef, CodexThreadSnapshot,
    CodexTurnOutcome, CodexTurnRef, EventType,
)


class FakeScenario(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    INTERRUPTED = "INTERRUPTED"
    SLOW_SUCCESS = "SLOW_SUCCESS"
    SERVER_BUSY = "SERVER_BUSY"
    TRANSPORT_ERROR = "TRANSPORT_ERROR"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"


class FakeCodexAdapter:
    def __init__(self, scenario: FakeScenario = FakeScenario.SUCCESS) -> None:
        self.scenario = scenario
        self.calls: list[str] = []
        self._thread_count = 0
        self._turn_count = 0
        self._names: dict[str, str] = {}
        self._turns: dict[str, str] = {}
        self._interrupted: set[str] = set()

    async def create_thread(self, config: CodexExecutionConfig) -> CodexThreadRef:
        self.calls.append("create_thread")
        self._thread_count += 1
        return CodexThreadRef(thread_id=f"fake-thread-{self._thread_count}")

    async def resume_thread(self, thread: CodexThreadRef) -> CodexThreadRef:
        self.calls.append("resume_thread")
        return thread

    async def start_turn(self, thread: CodexThreadRef, prompt: str) -> CodexTurnRef:
        self.calls.append("start_turn")
        self._turn_count += 1
        turn = CodexTurnRef(thread_id=thread.thread_id, turn_id=f"fake-turn-{self._turn_count}")
        self._turns[turn.turn_id] = thread.thread_id
        return turn

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.calls.append("stream_turn")
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        terminal = self._terminal_event(turn.turn_id)
        yield CodexEvent(event_type=terminal, thread_id=turn.thread_id, turn_id=turn.turn_id)

    async def interrupt_turn(self, turn: CodexTurnRef) -> CodexTurnOutcome:
        self.calls.append("interrupt_turn")
        self._interrupted.add(turn.turn_id)
        return CodexTurnOutcome(thread_id=turn.thread_id, turn_id=turn.turn_id, terminal_event=EventType.TURN_INTERRUPTED)

    async def read_thread(self, thread: CodexThreadRef) -> CodexThreadSnapshot:
        self.calls.append("read_thread")
        return CodexThreadSnapshot(thread=thread, name=self._names.get(thread.thread_id))

    async def set_thread_name(self, thread: CodexThreadRef, name: str) -> None:
        self.calls.append("set_thread_name")
        self._names[thread.thread_id] = name

    async def close(self) -> None:
        self.calls.append("close")

    def _terminal_event(self, turn_id: str) -> EventType:
        if turn_id in self._interrupted or self.scenario is FakeScenario.INTERRUPTED:
            return EventType.TURN_INTERRUPTED
        mapping = {
            FakeScenario.SUCCESS: EventType.TURN_COMPLETED,
            FakeScenario.SLOW_SUCCESS: EventType.TURN_COMPLETED,
            FakeScenario.FAILED: EventType.TURN_FAILED,
            FakeScenario.SERVER_BUSY: EventType.ATTENTION_REQUIRED,
            FakeScenario.TRANSPORT_ERROR: EventType.TRANSPORT_ERROR,
            FakeScenario.NEEDS_ATTENTION: EventType.ATTENTION_REQUIRED,
        }
        return mapping[self.scenario]
