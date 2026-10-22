"""Public SDK-independent API data-transfer models."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from codex_flow.application.control_contract import ControlAction
from codex_flow.domain.models import WorkflowDefinition
from codex_flow.domain.status import TaskStatus


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class WorkflowSummary(BaseModel):
    id: str
    name: str


class WorkflowDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    workflow: WorkflowDefinition


class WorkflowExportResponse(BaseModel):
    kind: Literal["codex_flow.workflow_definition"]
    schema_version: Literal[1]
    workflow: WorkflowDefinition


class RunStartResponse(BaseModel):
    run_id: str


class RunSummary(BaseModel):
    id: str
    workflow_id: str
    status: str
    created_at: str


class RunDetail(RunSummary):
    snapshot: dict[str, Any] = Field(default_factory=dict)


class TaskRunView(BaseModel):
    id: str
    workflow_run_id: str
    task_id: str
    status: str
    thread_id: str | None = None
    turn_id: str | None = None
    created_at: str


class AttemptView(BaseModel):
    id: str
    task_run_id: str
    status: str
    thread_id: str | None = None
    turn_id: str | None = None
    created_at: str


class EventView(BaseModel):
    id: str
    workflow_run_id: str | None = None
    task_run_id: str | None = None
    attempt_id: str | None = None
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class ManualActionResponse(BaseModel):
    """Public serialization of an accepted or rejected manual action."""

    action: ControlAction
    run_id: str
    task_id: str | None = None
    accepted: bool
    previous_status: TaskStatus | None = None
    status: TaskStatus | None = None
    retry_requested: bool = False
    error_code: str | None = None
    message: str | None = None


class RunControlState(BaseModel):
    """Durable workflow-run control state exposed without SDK objects."""

    run_id: str
    paused: bool
    paused_at: str | None = None
