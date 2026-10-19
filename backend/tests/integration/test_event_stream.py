import asyncio

from codex_flow.application.event_stream import EventStream
from codex_flow.application.events import EventApplicationService
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


async def test_stream_cancellation_does_not_change_durable_state(tmp_path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    repository.save_workflow_definition(
        WorkflowDefinition(
            id="workflow",
            name="Workflow",
            tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".")],
            edges=[],
        )
    )
    run_id = repository.create_workflow_run("workflow", {})
    repository.create_task_runs(run_id, ["A"])
    consumer = asyncio.create_task(EventStream(EventApplicationService(repository), 0.01).stream(run_id).__anext__())
    await asyncio.sleep(0.02)
    consumer.cancel()
    try:
        await consumer
    except asyncio.CancelledError:
        pass
    assert repository.get_workflow_run(run_id)["status"] == "PENDING"
