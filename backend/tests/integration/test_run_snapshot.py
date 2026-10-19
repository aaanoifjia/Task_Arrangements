from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.storage.snapshots import create_run_snapshot


def test_run_snapshot_is_immutable_after_definition_changes() -> None:
    workflow = WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="original", cwd=".")],
        edges=[],
    )

    snapshot = create_run_snapshot(workflow)
    workflow.tasks[0].prompt = "changed"

    task = snapshot["tasks"][0]
    assert task["prompt"] == "original"
    assert task["dependencies"] == []
    assert task["sandbox"] == "workspace_write"
