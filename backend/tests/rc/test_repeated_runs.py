"""Repeated durable workflow execution isolation checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.runtime.runner import DurableRunner
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def repeated_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="repeated-workflow",
        name="Repeated Workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="repeat", cwd=".")],
        edges=[],
    )


@pytest.mark.asyncio
async def test_repeated_runs_keep_distinct_durable_identities_and_events(tmp_path: Path) -> None:
    connection = open_database(tmp_path / "repeated.sqlite3")
    try:
        repository = StorageRepositories(connection)
        adapter = FakeCodexAdapter()
        runner = DurableRunner(repository, adapter)
        workflow = repeated_workflow()

        first_run_id = await runner.run(workflow)
        second_run_id = await runner.run(workflow)

        assert first_run_id != second_run_id
        runs = repository.list_workflow_runs(workflow.id)
        assert {row["id"] for row in runs} == {first_run_id, second_run_id}
        task_rows = {
            run_id: repository.load_task_runs(run_id)[0]
            for run_id in (first_run_id, second_run_id)
        }
        assert all(row["status"] == TaskStatus.SUCCESS.value for row in task_rows.values())
        assert task_rows[first_run_id]["id"] != task_rows[second_run_id]["id"]
        assert task_rows[first_run_id]["workflow_run_id"] == first_run_id
        assert task_rows[second_run_id]["workflow_run_id"] == second_run_id
        assert task_rows[first_run_id]["thread_id"] != task_rows[second_run_id]["thread_id"]
        assert task_rows[first_run_id]["turn_id"] != task_rows[second_run_id]["turn_id"]
        for task_row in task_rows.values():
            attempts = repository.load_attempts(str(task_row["id"]))
            assert len(attempts) == 1
            assert attempts[0]["thread_id"] == task_row["thread_id"]
            assert attempts[0]["turn_id"] == task_row["turn_id"]
            events = connection.execute(
                "SELECT event_type, task_run_id FROM events WHERE task_run_id = ? ORDER BY rowid",
                (task_row["id"],),
            ).fetchall()
            assert [event["event_type"] for event in events] == ["TURN_STARTED", "TURN_COMPLETED"]
            assert all(event["task_run_id"] == task_row["id"] for event in events)
        assert adapter.calls.count("create_thread") == 2
        assert adapter.calls.count("start_turn") == 2
    finally:
        connection.close()
