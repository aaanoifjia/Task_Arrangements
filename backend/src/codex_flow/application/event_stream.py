"""Cancellable polling stream over durable events and task snapshots."""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from codex_flow.application.events import EventApplicationService


@dataclass(frozen=True)
class StreamMessage:
    kind: str
    payload: dict[str, Any]


class EventStream:
    def __init__(
        self,
        service: EventApplicationService,
        poll_interval_seconds: float = 0.25,
        batch_size: int = 256,
    ) -> None:
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        self._service = service
        self._poll_interval_seconds = poll_interval_seconds
        self._batch_size = batch_size

    async def stream(
        self, run_id: str, after_event_id: str | None = None
    ) -> AsyncIterator[StreamMessage]:
        cursor = after_event_id
        previous_snapshot: list[dict[str, Any]] | None = None
        while True:
            events = self._service.list_events(run_id, cursor)
            batch = events[: self._batch_size]
            for event in batch:
                cursor = event.id
                yield StreamMessage(kind="event", payload=event.model_dump())

            if len(events) > len(batch):
                continue

            snapshot = [task.model_dump() for task in self._service.task_snapshot(run_id)]
            if snapshot != previous_snapshot:
                previous_snapshot = snapshot
                yield StreamMessage(kind="snapshot", payload={"tasks": snapshot})

            if self._service.run_is_terminal(run_id):
                return
            await asyncio.sleep(self._poll_interval_seconds)
