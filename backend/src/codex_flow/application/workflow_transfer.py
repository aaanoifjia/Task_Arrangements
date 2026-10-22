"""Deterministic import/export primitives for workflow definitions."""

import json
from collections.abc import Mapping
from typing import Any

from codex_flow.domain.models import WorkflowDefinition
from codex_flow.scheduler.graph import validate_workflow

WORKFLOW_EXPORT_KIND = "codex_flow.workflow_definition"
WORKFLOW_EXPORT_SCHEMA_VERSION = 1


class WorkflowImportError(ValueError):
    """Raised when a workflow export is not a supported valid envelope."""


def serialize_workflow_definition(workflow: WorkflowDefinition) -> str:
    """Return a stable, versioned envelope containing definition data only."""

    validated = WorkflowDefinition.model_validate(workflow.model_dump())
    envelope = {
        "kind": WORKFLOW_EXPORT_KIND,
        "schema_version": WORKFLOW_EXPORT_SCHEMA_VERSION,
        "workflow": validated.model_dump(mode="json"),
    }
    return json.dumps(envelope, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def parse_workflow_definition_export(payload: str | Mapping[str, Any]) -> WorkflowDefinition:
    """Parse and canonically validate a versioned workflow export envelope."""

    try:
        envelope: Any = json.loads(payload) if isinstance(payload, str) else payload
    except json.JSONDecodeError as exc:
        raise WorkflowImportError("invalid workflow export JSON") from exc

    if not isinstance(envelope, Mapping):
        raise WorkflowImportError("workflow export must be an object")
    if envelope.get("kind") != WORKFLOW_EXPORT_KIND:
        raise WorkflowImportError("unsupported workflow export kind")
    if envelope.get("schema_version") != WORKFLOW_EXPORT_SCHEMA_VERSION or isinstance(
        envelope.get("schema_version"), bool,
    ):
        raise WorkflowImportError("unsupported workflow export schema version")

    raw_workflow = envelope.get("workflow")
    if not isinstance(raw_workflow, Mapping):
        raise WorkflowImportError("workflow export workflow must be an object")
    try:
        workflow = WorkflowDefinition.model_validate(raw_workflow)
        validate_workflow(workflow)
    except (TypeError, ValueError) as exc:
        raise WorkflowImportError("malformed workflow definition") from exc
    return workflow
