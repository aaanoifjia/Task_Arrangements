"""REST endpoints for durable workflow-run controls."""

from fastapi import APIRouter, Request

from codex_flow.api.errors import api_error, conflict, not_found
from codex_flow.api.lifespan import get_repositories
from codex_flow.api.schemas import ManualActionResponse
from codex_flow.application.control_contract import ControlAction, ControlCommand
from codex_flow.application.controls import (
    ControlApplicationService,
    ControlConflictError,
    ControlNotFoundError,
    InvalidControlActionError,
)
from codex_flow.runtime.manager import RuntimeManager

router = APIRouter(prefix="/api", tags=["controls"])


def service(request: Request) -> ControlApplicationService:
    runtime = getattr(request.app.state, "runtime", None)
    if not isinstance(runtime, RuntimeManager):
        raise api_error(503, "RUNTIME_UNAVAILABLE", "runtime manager is not configured")
    return ControlApplicationService(runtime)


@router.post("/runs/{run_id}/pause", response_model=ManualActionResponse)
async def pause_run(request: Request, run_id: str) -> ManualActionResponse:
    command = ControlCommand(run_id=run_id, action=ControlAction.PAUSE)
    try:
        result = await service(request).apply(command)
    except ControlNotFoundError as error:
        raise not_found("CONTROL_RUN_NOT_FOUND", str(error)) from error
    except ControlConflictError as error:
        raise conflict("CONTROL_CONFLICT", str(error)) from error
    except InvalidControlActionError as error:
        raise api_error(422, "INVALID_CONTROL_ACTION", str(error)) from error
    return ManualActionResponse.model_validate(result.model_dump())


@router.post("/runs/{run_id}/resume", response_model=ManualActionResponse)
async def resume_run(request: Request, run_id: str) -> ManualActionResponse:
    command = ControlCommand(run_id=run_id, action=ControlAction.RESUME)
    try:
        result = await service(request).apply(command)
    except ControlNotFoundError as error:
        raise not_found("CONTROL_RUN_NOT_FOUND", str(error)) from error
    except ControlConflictError as error:
        raise conflict("CONTROL_CONFLICT", str(error)) from error
    except InvalidControlActionError as error:
        raise api_error(422, "INVALID_CONTROL_ACTION", str(error)) from error
    return ManualActionResponse.model_validate(result.model_dump())


def _task_run_id(request: Request, run_id: str, task_id: str) -> str:
    """Accept either the public task id or its durable TaskRun id."""
    for row in get_repositories(request.app).load_task_runs(run_id):
        if row["id"] == task_id or row["task_id"] == task_id:
            return str(row["id"])
    return task_id


@router.post("/runs/{run_id}/tasks/{task_id}/retry", response_model=ManualActionResponse)
async def retry_task(request: Request, run_id: str, task_id: str) -> ManualActionResponse:
    command = ControlCommand(
        run_id=run_id,
        action=ControlAction.RETRY,
        task_id=_task_run_id(request, run_id, task_id),
    )
    try:
        result = await service(request).apply(command)
    except ControlNotFoundError as error:
        raise not_found("CONTROL_TASK_NOT_FOUND", str(error)) from error
    except ControlConflictError as error:
        raise conflict("CONTROL_CONFLICT", str(error)) from error
    except InvalidControlActionError as error:
        raise api_error(422, "INVALID_CONTROL_ACTION", str(error)) from error
    return ManualActionResponse.model_validate(result.model_dump())
