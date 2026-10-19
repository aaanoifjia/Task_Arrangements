"""Explicit FastAPI application construction."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from codex_flow.api.config import ServiceConfig
from codex_flow.api.lifespan import AdapterFactory, lifespan
from codex_flow.api.routes.controls import router as controls_router
from codex_flow.api.routes.runs import router as runs_router
from codex_flow.api.routes.system import router as system_router
from codex_flow.api.routes.workflows import router as workflows_router
from codex_flow.api.routes.ws import router as ws_router
from codex_flow.codex_adapter.interface import CodexAdapter


def create_app(
    config: ServiceConfig | None = None,
    adapter: CodexAdapter | None = None,
    adapter_factory: AdapterFactory | None = None,
) -> FastAPI:
    """Construct the local API without opening resources or starting a server."""
    service_config = config or ServiceConfig.default()
    if adapter is not None and adapter_factory is not None:
        raise ValueError("provide adapter or adapter_factory, not both")
    selected_factory = adapter_factory
    if adapter is not None:
        selected_factory = lambda: adapter

    @asynccontextmanager
    async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with lifespan(app, service_config, selected_factory):
            yield

    app = FastAPI(title="Codex Flow Local API", version="0.1.0", lifespan=app_lifespan)
    app.state.service_config = service_config
    app.include_router(workflows_router)
    app.include_router(runs_router)
    app.include_router(controls_router)
    app.include_router(ws_router)
    app.include_router(system_router)

    @app.exception_handler(Exception)
    async def internal_error(request: Request, error: Exception) -> JSONResponse:
        del request, error
        return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "internal server error"}})

    return app
