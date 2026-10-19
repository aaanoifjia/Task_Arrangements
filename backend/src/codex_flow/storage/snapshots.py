"""Immutable workflow-run snapshots."""

import json

from codex_flow.domain.models import WorkflowDefinition


def create_run_snapshot(workflow: WorkflowDefinition) -> dict[str, object]:
    """Copy the full frozen execution definition for one WorkflowRun."""
    return json.loads(workflow.model_dump_json())
