"""Workflow REST endpoints."""

import json

from fastapi import APIRouter, Request, status

from codex_flow.api.errors import invalid_request, not_found
from codex_flow.api.lifespan import get_repositories
from codex_flow.api.schemas import WorkflowDetail, WorkflowExportResponse, WorkflowSummary
from codex_flow.application.workflow_transfer import serialize_workflow_definition
from codex_flow.application.workflows import (
    WorkflowApplicationService,
    WorkflowIdMismatchError,
    WorkflowNotFoundError,
)
from codex_flow.domain.models import WorkflowDefinition

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


def service(request: Request) -> WorkflowApplicationService:
    return WorkflowApplicationService(get_repositories(request.app))


@router.post("", response_model=WorkflowDetail, status_code=status.HTTP_201_CREATED)
async def create_workflow(request: Request, workflow: WorkflowDefinition) -> WorkflowDetail:
    return WorkflowDetail(workflow=service(request).save(workflow))


@router.put("/{workflow_id}", response_model=WorkflowDetail)
async def update_workflow(request: Request, workflow_id: str, workflow: WorkflowDefinition) -> WorkflowDetail:
    try:
        return WorkflowDetail(workflow=service(request).update(workflow_id, workflow))
    except WorkflowIdMismatchError as error:
        raise invalid_request("WORKFLOW_ID_MISMATCH", str(error)) from error
    except WorkflowNotFoundError as error:
        raise not_found("WORKFLOW_NOT_FOUND", str(error)) from error


@router.get("", response_model=list[WorkflowSummary])
async def list_workflows(request: Request) -> list[WorkflowSummary]:
    return [WorkflowSummary(id=item.id, name=item.name) for item in service(request).list()]


@router.get("/{workflow_id}/export", response_model=WorkflowExportResponse)
async def export_workflow(request: Request, workflow_id: str) -> WorkflowExportResponse:
    try:
        workflow = service(request).get(workflow_id)
    except WorkflowNotFoundError as error:
        raise not_found("WORKFLOW_NOT_FOUND", str(error)) from error
    return WorkflowExportResponse.model_validate(json.loads(serialize_workflow_definition(workflow)))


@router.get("/{workflow_id}", response_model=WorkflowDetail)
async def get_workflow(request: Request, workflow_id: str) -> WorkflowDetail:
    try:
        return WorkflowDetail(workflow=service(request).get(workflow_id))
    except WorkflowNotFoundError as error:
        raise not_found("WORKFLOW_NOT_FOUND", str(error)) from error
