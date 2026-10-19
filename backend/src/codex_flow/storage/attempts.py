"""Transactional launch ordering for external Codex attempts."""

import sqlite3
from datetime import UTC, datetime
from uuid import uuid4

from codex_flow.codex_adapter.interface import CodexAdapter
from codex_flow.codex_adapter.models import CodexExecutionConfig, CodexTurnRef


def _now() -> str:
    return datetime.now(UTC).isoformat()


class AttemptStarter:
    """Persist an attempt before any external execution is requested."""

    def __init__(self, connection: sqlite3.Connection, adapter: CodexAdapter) -> None:
        self._connection = connection
        self._adapter = adapter

    async def start(
        self, task_run_id: str, config: CodexExecutionConfig, prompt: str
    ) -> tuple[str, CodexTurnRef]:
        attempt_id = str(uuid4())
        with self._connection:
            cursor = self._connection.execute(
                "UPDATE task_runs SET status = 'STARTING' WHERE id = ? AND status = 'READY'",
                (task_run_id,),
            )
            if cursor.rowcount != 1:
                raise ValueError("task run must be READY before an attempt starts")
            self._connection.execute(
                "INSERT INTO attempts(id, task_run_id, status, created_at) VALUES (?, ?, 'STARTING', ?)",
                (attempt_id, task_run_id, _now()),
            )

        thread = await self._adapter.create_thread(config)
        turn = await self._adapter.start_turn(thread, prompt)
        self._persist_external_refs(task_run_id, attempt_id, turn)
        return attempt_id, turn

    def _persist_external_refs(self, task_run_id: str, attempt_id: str, turn: CodexTurnRef) -> None:
        with self._connection:
            self._connection.execute(
                "UPDATE task_runs SET thread_id = ?, turn_id = ? WHERE id = ?",
                (turn.thread_id, turn.turn_id, task_run_id),
            )
            self._connection.execute(
                "UPDATE attempts SET thread_id = ?, turn_id = ? WHERE id = ?",
                (turn.thread_id, turn.turn_id, attempt_id),
            )
