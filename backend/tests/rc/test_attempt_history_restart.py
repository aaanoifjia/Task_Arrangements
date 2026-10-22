"""Attempt identity and history preservation across a storage restart."""

from __future__ import annotations

from pathlib import Path

from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def test_attempt_history_reopens_in_order_without_overwriting_refs(tmp_path: Path) -> None:
    database_path = tmp_path / "attempt-history.sqlite3"
    workflow = WorkflowDefinition(
        id="attempt-history-workflow",
        name="Attempt History Workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".")],
        edges=[],
    )
    connection = open_database(database_path)
    repository = StorageRepositories(connection)
    repository.save_workflow_definition(workflow)
    run_id = repository.create_workflow_run(workflow.id, workflow.model_dump(mode="json"))
    task_run_id = repository.create_task_runs(run_id, ["A"])[0]
    first_attempt_id = repository.create_attempt(task_run_id)
    second_attempt_id = repository.create_attempt(task_run_id)
    connection.execute(
        """
        UPDATE attempts
        SET status = ?, thread_id = ?, turn_id = ?, created_at = ?
        WHERE id = ?
        """,
        ("FAILED", "thread-first", "turn-first", "2026-01-01T00:00:01+00:00", first_attempt_id),
    )
    connection.execute(
        """
        UPDATE attempts
        SET status = ?, thread_id = ?, turn_id = ?, created_at = ?
        WHERE id = ?
        """,
        ("SUCCESS", "thread-second", "turn-second", "2026-01-01T00:00:02+00:00", second_attempt_id),
    )
    repository.update_task_run_state(task_run_id, "SUCCESS", "thread-second", "turn-second")
    repository.update_workflow_run_state(run_id, "SUCCESS")
    connection.commit()
    before_restart = [
        (row["id"], row["status"], row["thread_id"], row["turn_id"])
        for row in repository.load_attempts(task_run_id)
    ]
    connection.close()

    reopened_connection = open_database(database_path)
    try:
        reopened = StorageRepositories(reopened_connection)
        reopened_attempts = reopened.load_attempts(task_run_id)
        after_restart = [
            (row["id"], row["status"], row["thread_id"], row["turn_id"])
            for row in reopened_attempts
        ]

        assert after_restart == before_restart
        assert [row["id"] for row in reopened_attempts] == [first_attempt_id, second_attempt_id]
        assert reopened.get_task_run(task_run_id)["thread_id"] == "thread-second"
        assert reopened.get_workflow_run(run_id)["status"] == "SUCCESS"
    finally:
        reopened_connection.close()
