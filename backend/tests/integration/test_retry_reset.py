import json
from pathlib import Path

import pytest

from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def _repository(tmp_path: Path) -> tuple[StorageRepositories, str, str]:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    repository.save_workflow_definition(
        WorkflowDefinition(
            id="workflow",
            name="Workflow",
            tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".")],
            edges=[],
        )
    )
    run_id = repository.create_workflow_run("workflow", {"workflow": "snapshot"})
    task_run_id = repository.create_task_runs(run_id, ["A"])[0]
    return repository, run_id, task_run_id


def test_retry_reset_preserves_attempts_clears_refs_and_audits(tmp_path: Path) -> None:
    repository, run_id, task_run_id = _repository(tmp_path)
    attempt_id = repository.create_attempt(task_run_id)
    repository.update_task_run_state(task_run_id, "FAILED", "thread-1", "turn-1")

    event_id = repository.reset_task_for_retry(task_run_id)

    task_run = repository.get_task_run(task_run_id)
    assert task_run is not None
    assert task_run["status"] == "PENDING"
    assert task_run["thread_id"] is None
    assert task_run["turn_id"] is None
    assert [row["id"] for row in repository.load_attempts(task_run_id)] == [attempt_id]
    event = repository.load_events_for_run(run_id)[0]
    assert event["id"] == event_id
    assert event["event_type"] == "RETRY_REQUESTED"
    assert json.loads(event["payload_json"]) == {
        "previous_status": "FAILED",
        "target_status": "PENDING",
        "task_id": "A",
    }


@pytest.mark.parametrize("status", ["PENDING", "READY", "RUNNING", "SUCCESS", "CANCELLED"])
def test_retry_reset_rejects_invalid_source_states(tmp_path: Path, status: str) -> None:
    repository, run_id, task_run_id = _repository(tmp_path)
    repository.update_task_run_state(task_run_id, status, "thread-1", "turn-1")

    with pytest.raises(ValueError, match="retry reset is not allowed"):
        repository.reset_task_for_retry(task_run_id)

    task_run = repository.get_task_run(task_run_id)
    assert task_run is not None and task_run["status"] == status
    assert repository.load_attempts(task_run_id) == []
    assert repository.load_events_for_run(run_id) == []
