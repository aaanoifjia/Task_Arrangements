"""Workflow REST endpoints."""

import json

from fastapi import APIRouter, Request, status

from codex_flow.api.errors import conflict, invalid_request, not_found
from codex_flow.api.lifespan import get_repositories
from codex_flow.api.schemas import (
    WorkflowDetail,
    WorkflowExportResponse,
    WorkflowImportRequest,
    WorkflowSummary,
)
from codex_flow.application.workflow_transfer import (
    WorkflowImportConflictError,
    WorkflowImportError,
    parse_workflow_definition_export,
    resolve_import_identity,
    serialize_workflow_definition,
)
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


@router.post("/import", response_model=WorkflowDetail, status_code=status.HTTP_201_CREATED)
async def import_workflow(request: Request) -> WorkflowDetail:
    try:
        payload = WorkflowImportRequest.model_validate(await request.json())
    except (TypeError, ValueError) as error:
        raise invalid_request("INVALID_WORKFLOW_IMPORT", "malformed workflow import request") from error
    try:
        workflow = parse_workflow_definition_export(payload.model_dump(exclude={"replacement_id"}))
        existing_ids = {item.id for item in service(request).list()}
        resolved = resolve_import_identity(workflow, existing_ids, replacement_id=payload.replacement_id)
        return WorkflowDetail(workflow=service(request).save(resolved))
    except WorkflowImportConflictError as error:
        raise conflict("WORKFLOW_IMPORT_CONFLICT", str(error)) from error
    except WorkflowImportError as error:
        raise invalid_request("INVALID_WORKFLOW_IMPORT", str(error)) from error


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
