"""Transactional launch ordering for external Codex attempts."""

import logging
import sqlite3
import time
from datetime import UTC, datetime
from uuid import uuid4

from codex_flow.codex_adapter.interface import CodexAdapter
from codex_flow.codex_adapter.models import CodexExecutionConfig, CodexThreadRef, CodexTurnRef

LOGGER = logging.getLogger("codex_flow.server")


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

        started_at = time.perf_counter()
        LOGGER.info("ATTEMPT_START_PERSISTED task_run_id=%s attempt_id=%s", task_run_id, attempt_id)
        LOGGER.info("CODEX_CREATE_THREAD_BEGIN task_run_id=%s attempt_id=%s", task_run_id, attempt_id)
        try:
            thread = await self._adapter.create_thread(config)
        except Exception:
            LOGGER.exception(
                "CODEX_CREATE_THREAD_FAILED task_run_id=%s attempt_id=%s elapsed_ms=%d",
                task_run_id, attempt_id, (time.perf_counter() - started_at) * 1000,
            )
            raise
        LOGGER.info(
            "CODEX_CREATE_THREAD_OK task_run_id=%s attempt_id=%s thread_id=%s elapsed_ms=%d",
            task_run_id, attempt_id, thread.thread_id, (time.perf_counter() - started_at) * 1000,
        )
        LOGGER.info(
            "CODEX_START_TURN_BEGIN task_run_id=%s attempt_id=%s thread_id=%s",
            task_run_id, attempt_id, thread.thread_id,
        )
        try:
            turn = await self._adapter.start_turn(thread, prompt)
        except Exception:
            LOGGER.exception(
                "CODEX_START_TURN_FAILED task_run_id=%s attempt_id=%s thread_id=%s elapsed_ms=%d",
                task_run_id, attempt_id, thread.thread_id, (time.perf_counter() - started_at) * 1000,
            )
            raise
        LOGGER.info(
            "CODEX_START_TURN_OK task_run_id=%s attempt_id=%s thread_id=%s turn_id=%s elapsed_ms=%d",
            task_run_id, attempt_id, turn.thread_id, turn.turn_id, (time.perf_counter() - started_at) * 1000,
        )
        self._persist_external_refs(task_run_id, attempt_id, turn)
        return attempt_id, turn

    async def start_continuation(
        self, task_run_id: str, source_thread_id: str, prompt: str
    ) -> tuple[str, CodexTurnRef]:
        """Persist a continuation attempt before resuming its external thread."""
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

        started_at = time.perf_counter()
        LOGGER.info(
            "ATTEMPT_START_PERSISTED task_run_id=%s attempt_id=%s continuation=true",
            task_run_id, attempt_id,
        )
        LOGGER.info(
            "CODEX_CREATE_THREAD_BEGIN task_run_id=%s attempt_id=%s continuation=true source_thread_id=%s",
            task_run_id, attempt_id, source_thread_id,
        )
        try:
            thread = await self._adapter.resume_thread(CodexThreadRef(thread_id=source_thread_id))
        except Exception:
            LOGGER.exception(
                "CODEX_CREATE_THREAD_FAILED task_run_id=%s attempt_id=%s continuation=true elapsed_ms=%d",
                task_run_id, attempt_id, (time.perf_counter() - started_at) * 1000,
            )
            raise
        if thread.thread_id != source_thread_id:
            raise ValueError("continuation adapter changed the source thread")
        LOGGER.info(
            "CODEX_CREATE_THREAD_OK task_run_id=%s attempt_id=%s continuation=true thread_id=%s elapsed_ms=%d",
            task_run_id, attempt_id, thread.thread_id, (time.perf_counter() - started_at) * 1000,
        )
        LOGGER.info(
            "CODEX_START_TURN_BEGIN task_run_id=%s attempt_id=%s thread_id=%s continuation=true",
            task_run_id, attempt_id, thread.thread_id,
        )
        try:
            turn = await self._adapter.start_turn(thread, prompt)
        except Exception:
            LOGGER.exception(
                "CODEX_START_TURN_FAILED task_run_id=%s attempt_id=%s thread_id=%s elapsed_ms=%d",
                task_run_id, attempt_id, thread.thread_id, (time.perf_counter() - started_at) * 1000,
            )
            raise
        LOGGER.info(
            "CODEX_START_TURN_OK task_run_id=%s attempt_id=%s thread_id=%s turn_id=%s elapsed_ms=%d",
            task_run_id, attempt_id, turn.thread_id, turn.turn_id, (time.perf_counter() - started_at) * 1000,
        )
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
