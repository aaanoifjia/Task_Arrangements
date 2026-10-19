from codex_flow.application.control_contract import ControlAction, ControlCommand, accepted_result
from codex_flow.application.event_stream import EventStream
from codex_flow.application.events import EventApplicationService
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


async def test_manual_control_audits_stream_in_order_and_reconnect_without_duplicates(tmp_path) -> None:
    connection = open_database(tmp_path / "flow.sqlite3")
    repository = StorageRepositories(connection)
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
    controls = [
        accepted_result(ControlCommand(run_id=run_id, action=ControlAction.PAUSE)),
        accepted_result(
            ControlCommand(run_id=run_id, action=ControlAction.RETRY, task_id=task_run_id),
            previous_status=TaskStatus.FAILED,
        ),
        accepted_result(
            ControlCommand(run_id=run_id, action=ControlAction.CANCEL, task_id=task_run_id),
            previous_status=TaskStatus.READY,
        ),
    ]
    event_ids = [
        repository.append_manual_action_audit(result, task_run_id=task_run_id)
        for result in controls
    ]
    repository.update_workflow_run_state(run_id, TaskStatus.SUCCESS.value)

    service = EventApplicationService(repository)
    messages = [message async for message in EventStream(service).stream(run_id)]
    audit_messages = [message for message in messages if message.kind == "event"]

    ordered_event_ids = [message.payload["id"] for message in audit_messages]
    assert set(ordered_event_ids) == set(event_ids)
    assert [message.payload["event_type"] for message in audit_messages] == [
        "MANUAL_ACTION_ACCEPTED",
        "MANUAL_ACTION_ACCEPTED",
        "MANUAL_ACTION_ACCEPTED",
    ]
    assert all(message.payload["workflow_run_id"] == run_id for message in audit_messages)
    assert {message.payload["payload"]["action"] for message in audit_messages} == {
        "PAUSE",
        "RETRY",
        "CANCEL",
    }

    resumed = [
        message
        async for message in EventStream(service).stream(
            run_id, after_event_id=ordered_event_ids[0]
        )
    ]
    resumed_events = [message for message in resumed if message.kind == "event"]
    assert [message.payload["id"] for message in resumed_events] == ordered_event_ids[1:]
    assert ordered_event_ids[0] not in [message.payload["id"] for message in resumed_events]
