"""Manual controls and durable restart matrix for M11."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexTurnRef, EventType
from codex_flow.domain.models import Edge, TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.runtime.manager import RuntimeManager
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="control-restart-workflow",
        name="Control Restart Workflow",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="parent", cwd="."),
            TaskDefinition(id="B", name="B", prompt="child", cwd=".", dependencies=["A"]),
        ],
        edges=[Edge(source_task_id="A", target_task_id="B")],
    )


def seed_run(
    database_path: Path,
    *,
    parent_status: TaskStatus,
    child_status: TaskStatus,
    run_status: TaskStatus = TaskStatus.RUNNING,
) -> tuple[str, str, str]:
    connection = open_database(database_path)
    repository = StorageRepositories(connection)
    definition = workflow()
    repository.save_workflow_definition(definition)
    run_id = repository.create_workflow_run(definition.id, definition.model_dump(mode="json"))
    parent_id, child_id = repository.create_task_runs(run_id, ["A", "B"])
    repository.update_workflow_run_state(run_id, run_status.value)
    repository.update_task_run_state(parent_id, parent_status.value)
    repository.update_task_run_state(child_id, child_status.value)
    connection.close()
    return run_id, parent_id, child_id


@pytest.mark.asyncio
async def test_pause_resume_across_recreation_requires_explicit_resume(tmp_path: Path) -> None:
    database_path = tmp_path / "pause-resume.sqlite3"
    run_id, _, _ = seed_run(
        database_path, parent_status=TaskStatus.PENDING, child_status=TaskStatus.PENDING
    )

    first_connection = open_database(database_path)
    first_repository = StorageRepositories(first_connection)
    first_adapter = FakeCodexAdapter()
    first_manager = RuntimeManager(first_repository, first_adapter)
    first_manager.restore_workflow(run_id, workflow())
    paused = await first_manager.pause(run_id)
    assert paused.accepted
    assert first_repository.get_workflow_run_paused(run_id)
    first_connection.close()

    restarted_connection = open_database(database_path)
    try:
        restarted_repository = StorageRepositories(restarted_connection)
        adapter = FakeCodexAdapter()
        manager = RuntimeManager(restarted_repository, adapter)
        manager.restore_workflow(run_id, workflow())
        assert restarted_repository.get_workflow_run_paused(run_id)
        resumed = await manager.resume(run_id)
        await manager.wait(run_id)

        assert resumed.accepted
        assert adapter.calls.count("create_thread") == 2
        assert not restarted_repository.get_workflow_run_paused(run_id)
        assert restarted_repository.get_workflow_run(run_id)["status"] == TaskStatus.SUCCESS.value
        assert [event["event_type"] for event in restarted_repository.load_events_for_run(run_id)] == [
            "MANUAL_ACTION_ACCEPTED",
            "MANUAL_ACTION_ACCEPTED",
        ]
    finally:
        restarted_connection.close()


@pytest.mark.asyncio
async def test_queued_cancel_after_recreation_keeps_child_unreleased(tmp_path: Path) -> None:
    database_path = tmp_path / "cancel-queued.sqlite3"
    run_id, parent_id, child_id = seed_run(
        database_path, parent_status=TaskStatus.READY, child_status=TaskStatus.PENDING
    )
    connection = open_database(database_path)
    try:
        repository = StorageRepositories(connection)
        adapter = FakeCodexAdapter()
        manager = RuntimeManager(repository, adapter)
        manager.restore_workflow(run_id, workflow())

        result = await manager.cancel(run_id, parent_id)

        assert result.accepted
        assert repository.get_task_run(parent_id)["status"] == TaskStatus.CANCELLED.value
        assert repository.get_task_run(child_id)["status"] == TaskStatus.PENDING.value
        assert adapter.calls == []
        assert repository.load_events_for_run(run_id)[-1]["event_type"] == "MANUAL_ACTION_ACCEPTED"
    finally:
        connection.close()


@pytest.mark.asyncio
async def test_skip_after_recreation_keeps_child_blocked(tmp_path: Path) -> None:
    database_path = tmp_path / "skip-queued.sqlite3"
    run_id, parent_id, child_id = seed_run(
        database_path, parent_status=TaskStatus.READY, child_status=TaskStatus.BLOCKED
    )
    connection = open_database(database_path)
    try:
        repository = StorageRepositories(connection)
        adapter = FakeCodexAdapter()
        manager = RuntimeManager(repository, adapter)
        manager.restore_workflow(run_id, workflow())

        result = await manager.skip(run_id, parent_id)

        assert result.accepted
        assert repository.get_task_run(parent_id)["status"] == TaskStatus.SKIPPED.value
        assert repository.get_task_run(child_id)["status"] == TaskStatus.BLOCKED.value
        assert adapter.calls == []
        assert repository.load_events_for_run(run_id)[-1]["event_type"] == "MANUAL_ACTION_ACCEPTED"
    finally:
        connection.close()


@pytest.mark.asyncio
async def test_mark_success_after_recreation_releases_child_and_audits(tmp_path: Path) -> None:
    database_path = tmp_path / "mark-success.sqlite3"
    run_id, parent_id, child_id = seed_run(
        database_path, parent_status=TaskStatus.READY, child_status=TaskStatus.PENDING
    )
    connection = open_database(database_path)
    try:
        repository = StorageRepositories(connection)
        adapter = FakeCodexAdapter()
        manager = RuntimeManager(repository, adapter)
        manager.restore_workflow(run_id, workflow())

        result = await manager.mark_success(run_id, parent_id)
        await manager.wait(run_id)

        assert result.accepted
        assert repository.get_task_run(parent_id)["status"] == TaskStatus.SUCCESS.value
        assert repository.get_task_run(child_id)["status"] == TaskStatus.SUCCESS.value
        assert adapter.calls.count("create_thread") == 1
        assert repository.load_events_for_run(run_id)[-1]["event_type"] == "MANUAL_ACTION_ACCEPTED"
    finally:
        connection.close()


@pytest.mark.asyncio
async def test_retry_after_recreation_releases_child_once(tmp_path: Path) -> None:
    database_path = tmp_path / "retry.sqlite3"
    run_id, parent_id, child_id = seed_run(
        database_path,
        parent_status=TaskStatus.FAILED,
        child_status=TaskStatus.BLOCKED,
        run_status=TaskStatus.FAILED,
    )
    connection = open_database(database_path)
    try:
        repository = StorageRepositories(connection)
        adapter = FakeCodexAdapter()
        manager = RuntimeManager(repository, adapter)
        manager.restore_workflow(run_id, workflow())

        result = await manager.retry(run_id, parent_id)
        await manager.wait(run_id)

        assert result.accepted
        assert repository.get_task_run(parent_id)["status"] == TaskStatus.SUCCESS.value
        assert repository.get_task_run(child_id)["status"] == TaskStatus.SUCCESS.value
        assert len(repository.load_attempts(parent_id)) == 1
        assert repository.load_events_for_run(run_id)[-1]["event_type"] == "MANUAL_ACTION_ACCEPTED"
    finally:
        connection.close()


class InterruptibleAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.calls.append("stream_turn")
        self.started.set()
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        await self.release.wait()
        yield CodexEvent(
            event_type=EventType.TURN_INTERRUPTED,
            thread_id=turn.thread_id,
            turn_id=turn.turn_id,
        )


@pytest.mark.asyncio
async def test_running_cancel_interrupts_once_and_preserves_canonical_state(tmp_path: Path) -> None:
    database_path = tmp_path / "cancel-running.sqlite3"
    definition = WorkflowDefinition(
        id="running-cancel-workflow",
        name="Running Cancel Workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="running", cwd=".")],
        edges=[],
    )
    connection = open_database(database_path)
    try:
        repository = StorageRepositories(connection)
        adapter = InterruptibleAdapter()
        manager = RuntimeManager(repository, adapter)
        run_id = await manager.start(definition)
        await adapter.started.wait()
        task_run_id = str(repository.load_task_runs(run_id)[0]["id"])

        result = await manager.cancel(run_id, task_run_id)
        duplicate = await manager.cancel(run_id, task_run_id)
        adapter.release.set()
        await manager.wait(run_id)

        assert result.accepted
        assert duplicate.accepted is False
        assert duplicate.error_code == "TASK_NOT_QUEUED"
        assert adapter.calls.count("interrupt_turn") == 1
        assert repository.get_task_run(task_run_id)["status"] == TaskStatus.CANCELLED.value
        assert [event["event_type"] for event in repository.load_events_for_run(run_id)] == [
            "MANUAL_ACTION_ACCEPTED",
            "MANUAL_ACTION_REJECTED",
        ]
    finally:
        connection.close()
