import pytest

from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def test_repository_query_operations_are_deterministic(tmp_path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    workflow = WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".")],
        edges=[],
    )
    repository.save_workflow_definition(workflow)
    run_id = repository.create_workflow_run("workflow", {"frozen": True})
    task_run_id = repository.create_task_runs(run_id, ["A"])[0]
    attempt_id = repository.create_attempt(task_run_id)
    repository.append_event("FIRST", {"n": 1}, workflow_run_id=run_id, task_run_id=task_run_id, attempt_id=attempt_id)
    second_id = repository.append_event("SECOND", {"n": 2}, workflow_run_id=run_id)

    assert [row["id"] for row in repository.list_workflows()] == ["workflow"]
    assert repository.get_workflow_run(run_id)["id"] == run_id
    assert repository.list_workflow_runs("workflow")[0]["id"] == run_id
    assert repository.get_task_run(task_run_id)["id"] == task_run_id
    assert repository.load_attempts(task_run_id)[0]["id"] == attempt_id
    assert repository.load_events_for_run(run_id)[-1]["id"] == second_id
    assert repository.load_events_after(run_id, second_id) == []


def test_missing_query_results_and_cursor_are_explicit(tmp_path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))

    assert repository.load_workflow("missing") is None
    assert repository.get_workflow_run("missing") is None
    assert repository.get_task_run("missing") is None
    with pytest.raises(ValueError, match="cursor"):
        repository.load_events_after("missing", "missing")
