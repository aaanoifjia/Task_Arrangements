import pytest

from codex_flow.application.workflows import (
    WorkflowApplicationService,
    WorkflowIdMismatchError,
    WorkflowNotFoundError,
)
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def workflow(name: str = "Workflow") -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow",
        name=name,
        tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".")],
        edges=[],
    )


def test_create_update_list_get_and_snapshot_isolation(tmp_path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    service = WorkflowApplicationService(repository)

    service.save(workflow())
    run_id = repository.create_workflow_run("workflow", {"name": "Workflow"})
    service.update("workflow", workflow("Edited"))

    assert service.get("workflow").name == "Edited"
    assert [item.name for item in service.list()] == ["Edited"]
    assert repository.get_workflow_run(run_id)["snapshot_json"] == '{"name": "Workflow"}'


def test_invalid_update_and_missing_workflow_are_translated(tmp_path) -> None:
    service = WorkflowApplicationService(StorageRepositories(open_database(tmp_path / "flow.sqlite3")))

    with pytest.raises(WorkflowIdMismatchError):
        service.update("other", workflow())
    with pytest.raises(WorkflowNotFoundError):
        service.update("workflow", workflow())
    with pytest.raises(WorkflowNotFoundError):
        service.get("missing")
