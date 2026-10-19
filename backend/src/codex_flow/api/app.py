"""Explicit FastAPI application construction."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from codex_flow.api.config import ServiceConfig
from codex_flow.api.lifespan import lifespan
from codex_flow.api.routes.runs import router as runs_router
from codex_flow.api.routes.workflows import router as workflows_router


def create_app(config: ServiceConfig | None = None) -> FastAPI:
    """Construct the local API without opening resources or starting a server."""
    service_config = config or ServiceConfig.default()

    @asynccontextmanager
    async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with lifespan(app, service_config):
            yield

    app = FastAPI(title="Codex Flow Local API", version="0.1.0", lifespan=app_lifespan)
    app.state.service_config = service_config
    app.include_router(workflows_router)
    app.include_router(runs_router)

    @app.exception_handler(Exception)
    async def internal_error(request: Request, error: Exception) -> JSONResponse:
        del request, error
        return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "internal server error"}})

    return app
