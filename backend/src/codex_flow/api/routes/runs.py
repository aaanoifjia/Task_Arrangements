"""Run and task REST endpoints."""

from fastapi import APIRouter, Request, status

from codex_flow.api.errors import api_error, conflict, not_found
from codex_flow.api.lifespan import get_repositories
from codex_flow.api.schemas import (
    AttemptView,
    RunDetail,
    RunStartResponse,
    RunSummary,
    TaskRunView,
)
from codex_flow.application.runs import (
    ActiveRunConflictError,
    RunApplicationService,
    RunNotFoundError,
    RunWorkflowNotFoundError,
)
from codex_flow.runtime.manager import RuntimeManager

router = APIRouter(prefix="/api", tags=["runs"])


def service(request: Request) -> RunApplicationService:
    runtime = getattr(request.app.state, "runtime", None)
    if not isinstance(runtime, RuntimeManager):
        raise api_error(503, "RUNTIME_UNAVAILABLE", "runtime manager is not configured")
    return RunApplicationService(get_repositories(request.app), runtime)


@router.post("/workflows/{workflow_id}/runs", response_model=RunStartResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_run(request: Request, workflow_id: str) -> RunStartResponse:
    try:
        return await service(request).start_workflow(workflow_id)
    except RunWorkflowNotFoundError as error:
        raise not_found("WORKFLOW_NOT_FOUND", str(error)) from error
    except ActiveRunConflictError as error:
        raise conflict("ACTIVE_RUN", str(error)) from error


@router.get("/runs", response_model=list[RunSummary])
async def list_runs(request: Request, workflow_id: str | None = None) -> list[RunSummary]:
    return service(request).list_runs(workflow_id)


@router.get("/runs/{run_id}", response_model=RunDetail)
async def get_run(request: Request, run_id: str) -> RunDetail:
    try:
        return service(request).get_run(run_id)
    except RunNotFoundError as error:
        raise not_found("RUN_NOT_FOUND", str(error)) from error


@router.get("/runs/{run_id}/tasks", response_model=list[TaskRunView])
async def list_tasks(request: Request, run_id: str) -> list[TaskRunView]:
    try:
        return service(request).list_task_runs(run_id)
    except RunNotFoundError as error:
        raise not_found("RUN_NOT_FOUND", str(error)) from error


def _task_view(service_instance: RunApplicationService, run_id: str, task_id: str) -> TaskRunView:
    for task in service_instance.list_task_runs(run_id):
        if task.task_id == task_id or task.id == task_id:
            return task
    raise RunNotFoundError(f"task run not found: {task_id}")


@router.get("/runs/{run_id}/tasks/{task_id}", response_model=TaskRunView)
async def get_task(request: Request, run_id: str, task_id: str) -> TaskRunView:
    try:
        return _task_view(service(request), run_id, task_id)
    except RunNotFoundError as error:
        raise not_found("TASK_RUN_NOT_FOUND", str(error)) from error


@router.get("/runs/{run_id}/tasks/{task_id}/attempts", response_model=list[AttemptView])
async def list_attempts(request: Request, run_id: str, task_id: str) -> list[AttemptView]:
    try:
        service_instance = service(request)
        task = _task_view(service_instance, run_id, task_id)
        return service_instance.list_attempts(run_id, task.id)
    except RunNotFoundError as error:
        raise not_found("TASK_RUN_NOT_FOUND", str(error)) from error
