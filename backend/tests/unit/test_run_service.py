import pytest

from codex_flow.application.runs import (
    ActiveRunConflictError,
    RunApplicationService,
    RunNotFoundError,
    RunWorkflowNotFoundError,
)
from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.runtime.manager import RuntimeManager
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".")],
        edges=[],
    )


async def test_start_and_query_run_task_and_attempt_history(tmp_path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    repository.save_workflow_definition(workflow())
    service = RunApplicationService(repository, RuntimeManager(repository, FakeCodexAdapter()))

    response = await service.start_workflow("workflow")
    await service._runtime.wait(response.run_id)

    assert service.get_run(response.run_id).status == "SUCCESS"
    task = service.list_task_runs(response.run_id)[0]
    assert task.status == "SUCCESS"
    assert len(service.list_attempts(response.run_id, task.id)) == 1


async def test_missing_and_duplicate_runs_are_translated(tmp_path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    repository.save_workflow_definition(workflow())
    runtime = RuntimeManager(repository, FakeCodexAdapter())
    service = RunApplicationService(repository, runtime)

    with pytest.raises(RunWorkflowNotFoundError):
        await service.start_workflow("missing")
    await service.start_workflow("workflow")
    with pytest.raises(ActiveRunConflictError):
        await service.start_workflow("workflow")
    with pytest.raises(RunNotFoundError):
        service.get_run("missing")
