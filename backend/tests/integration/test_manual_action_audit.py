import json
from pathlib import Path

from codex_flow.application.control_contract import (
    ControlAction,
    ControlCommand,
    accepted_result,
    rejected_result,
)
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def test_accepted_and_rejected_actions_are_append_only_audits(tmp_path: Path) -> None:
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

    accepted = accepted_result(
        ControlCommand(run_id=run_id, action=ControlAction.MARK_SUCCESS, task_id="A"),
        previous_status=TaskStatus.READY,
    )
    rejected = rejected_result(
        ControlCommand(run_id=run_id, action=ControlAction.RETRY, task_id="A"),
        error_code="INVALID_STATE",
        message="task is RUNNING",
    )
    repository.append_manual_action_audit(accepted, task_run_id=task_run_id)
    repository.append_manual_action_audit(rejected, task_run_id=task_run_id)

    events = repository.load_events_for_run(run_id)
    assert [row["event_type"] for row in events] == [
        "MANUAL_ACTION_ACCEPTED",
        "MANUAL_ACTION_REJECTED",
    ]
    assert json.loads(events[0]["payload_json"]) == {
        "accepted": True,
        "action": "MARK_SUCCESS",
        "previous_status": "READY",
        "retry_requested": False,
        "run_id": run_id,
        "target_status": "SUCCESS",
        "task_id": "A",
    }
    assert json.loads(events[1]["payload_json"]) == {
        "accepted": False,
        "action": "RETRY",
        "error_code": "INVALID_STATE",
        "message": "task is RUNNING",
        "previous_status": None,
        "retry_requested": False,
        "run_id": run_id,
        "target_status": None,
        "task_id": "A",
    }
    assert "credential" not in events[0]["payload_json"].lower()
    assert "credential" not in events[1]["payload_json"].lower()
