"""Canonical workflow definition export tests."""

import json

from codex_flow.application.workflow_transfer import (
    WORKFLOW_EXPORT_KIND,
    WORKFLOW_EXPORT_SCHEMA_VERSION,
    WorkflowImportError,
    parse_workflow_definition_export,
    serialize_workflow_definition,
)
from codex_flow.domain.models import Edge, TaskDefinition, WorkflowDefinition


def workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow-export",
        name="Export example",
        description="Definition-only fixture",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="Illustrative", cwd="."),
            TaskDefinition(id="B", name="B", prompt="Illustrative", cwd=".", dependencies=["A"]),
        ],
        edges=[Edge(source_task_id="A", target_task_id="B")],
    )


def test_export_is_a_stable_versioned_definition_only_envelope() -> None:
    source = workflow()
    exported = serialize_workflow_definition(source)
    envelope = json.loads(exported)

    assert list(envelope) == ["kind", "schema_version", "workflow"]
    assert envelope["kind"] == WORKFLOW_EXPORT_KIND
    assert envelope["schema_version"] == WORKFLOW_EXPORT_SCHEMA_VERSION
    assert envelope["workflow"]["id"] == source.id
    assert envelope["workflow"]["tasks"][1]["dependencies"] == ["A"]
    assert not any(key in envelope for key in ("runs", "attempts", "events", "task_runs"))


def test_export_is_deterministic_and_round_trips_definition_data() -> None:
    source = workflow()
    first = serialize_workflow_definition(source)
    second = serialize_workflow_definition(WorkflowDefinition.model_validate(source.model_dump()))

    assert first == second
    envelope = json.loads(first)
    restored = WorkflowDefinition.model_validate(envelope["workflow"])
    assert restored == source


def test_import_parses_valid_export_exactly() -> None:
    source = workflow()

    restored = parse_workflow_definition_export(serialize_workflow_definition(source))

    assert restored == source


def test_import_rejects_malformed_and_unsupported_envelopes() -> None:
    source = json.loads(serialize_workflow_definition(workflow()))

    for payload, message in [
        ("not-json", "invalid workflow export JSON"),
        ({**source, "schema_version": 2}, "unsupported workflow export schema version"),
        ({**source, "workflow": {"id": "missing-fields"}}, "malformed workflow definition"),
    ]:
        try:
            parse_workflow_definition_export(payload)
        except WorkflowImportError as exc:
            assert str(exc) == message
        else:
            raise AssertionError("expected WorkflowImportError")


def test_import_rejects_cyclic_graphs() -> None:
    source = json.loads(serialize_workflow_definition(workflow()))
    source["workflow"]["tasks"][0]["dependencies"] = ["B"]
    source["workflow"]["edges"].append({"source_task_id": "B", "target_task_id": "A"})

    try:
        parse_workflow_definition_export(source)
    except WorkflowImportError as exc:
        assert str(exc) == "malformed workflow definition"
    else:
        raise AssertionError("expected WorkflowImportError")
