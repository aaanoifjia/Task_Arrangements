from pathlib import Path

import pytest

from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def _repository(tmp_path: Path) -> tuple[StorageRepositories, str]:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    repository.save_workflow_definition(
        WorkflowDefinition(
            id="workflow",
            name="Workflow",
            tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".")],
            edges=[],
        )
    )
    return repository, repository.create_workflow_run("workflow", {"workflow": "snapshot"})


def test_pause_state_is_durable_and_has_metadata(tmp_path: Path) -> None:
    repository, run_id = _repository(tmp_path)

    assert repository.get_workflow_run_paused(run_id) is False
    repository.set_workflow_run_paused(run_id, True)
    row = repository.get_workflow_run(run_id)
    assert repository.get_workflow_run_paused(run_id) is True
    assert row is not None and row["paused_at"] is not None

    repository.set_workflow_run_paused(run_id, False)
    row = repository.get_workflow_run(run_id)
    assert repository.get_workflow_run_paused(run_id) is False
    assert row is not None and row["paused_at"] is None


def test_compare_state_update_fails_closed_for_stale_observation(tmp_path: Path) -> None:
    repository, run_id = _repository(tmp_path)
    task_run_id = repository.create_task_runs(run_id, ["A"])[0]

    assert repository.compare_and_update_task_run_state(task_run_id, "READY", "RUNNING") is False
    assert repository.get_task_run(task_run_id)["status"] == "PENDING"  # type: ignore[index]
    assert repository.compare_and_update_task_run_state(task_run_id, "PENDING", "READY") is True
    assert repository.compare_and_update_task_run_state(task_run_id, "PENDING", "RUNNING") is False
    assert repository.get_task_run(task_run_id)["status"] == "READY"  # type: ignore[index]


def test_control_repository_rejects_unknown_runs(tmp_path: Path) -> None:
    repository, _ = _repository(tmp_path)

    with pytest.raises(ValueError, match="workflow run not found"):
        repository.get_workflow_run_paused("missing")
    with pytest.raises(ValueError, match="workflow run not found"):
        repository.set_workflow_run_paused("missing", True)
