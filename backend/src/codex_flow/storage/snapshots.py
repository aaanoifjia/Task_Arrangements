"""Immutable workflow-run snapshots."""

import json
from typing import cast

from codex_flow.domain.models import WorkflowDefinition


def create_run_snapshot(workflow: WorkflowDefinition) -> dict[str, object]:
    """Copy the full frozen execution definition for one WorkflowRun."""
    return cast(dict[str, object], json.loads(workflow.model_dump_json()))
