"""Deterministic import/export primitives for workflow definitions."""

import json

from codex_flow.domain.models import WorkflowDefinition

WORKFLOW_EXPORT_KIND = "codex_flow.workflow_definition"
WORKFLOW_EXPORT_SCHEMA_VERSION = 1


def serialize_workflow_definition(workflow: WorkflowDefinition) -> str:
    """Return a stable, versioned envelope containing definition data only."""

    validated = WorkflowDefinition.model_validate(workflow.model_dump())
    envelope = {
        "kind": WORKFLOW_EXPORT_KIND,
        "schema_version": WORKFLOW_EXPORT_SCHEMA_VERSION,
        "workflow": validated.model_dump(mode="json"),
    }
    return json.dumps(envelope, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
