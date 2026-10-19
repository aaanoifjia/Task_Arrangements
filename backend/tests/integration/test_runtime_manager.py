import pytest

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


@pytest.mark.asyncio
async def test_start_returns_persisted_run_id_before_background_completion(tmp_path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    manager = RuntimeManager(repository, FakeCodexAdapter())

    run_id = await manager.start(workflow())

    assert repository.get_workflow_run(run_id) is not None
    await manager.wait(run_id)
    assert repository.get_workflow_run(run_id)["status"] == "SUCCESS"
    assert manager.active_count == 0


@pytest.mark.asyncio
async def test_second_active_start_is_rejected(tmp_path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    manager = RuntimeManager(repository, FakeCodexAdapter())

    await manager.start(workflow())

    with pytest.raises(ValueError, match="active run"):
        await manager.start(workflow())
