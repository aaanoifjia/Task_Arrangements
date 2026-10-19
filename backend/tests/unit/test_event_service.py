from codex_flow.application.event_stream import EventStream
from codex_flow.application.events import EventApplicationService
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def test_event_service_uses_durable_cursor_and_task_snapshot(tmp_path) -> None:
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
    task_run_id = repository.create_task_runs(run_id, ["A"])[0]
    event_id = repository.append_event("TURN_STARTED", {"turn": "t"}, workflow_run_id=run_id, task_run_id=task_run_id)

    service = EventApplicationService(repository)

    assert service.list_events(run_id)[0].id == event_id
    assert service.list_events(run_id, event_id) == []
    assert service.task_snapshot(run_id)[0].task_id == "A"


async def test_event_stream_emits_event_and_snapshot_then_finishes(tmp_path) -> None:
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
    task_run_id = repository.create_task_runs(run_id, ["A"])[0]
    repository.append_event("TURN_COMPLETED", {}, workflow_run_id=run_id, task_run_id=task_run_id)
    repository.update_workflow_run_state(run_id, "SUCCESS")

    messages = [message async for message in EventStream(EventApplicationService(repository)).stream(run_id)]

    assert [message.kind for message in messages] == ["event", "snapshot"]
