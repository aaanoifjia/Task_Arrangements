"""Explicit FastAPI application construction."""

import hmac
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

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
    if service_config.desktop_mode:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(service_config.cors_origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.middleware("http")
    async def local_token_middleware(request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Protect REST data endpoints when a desktop process token is configured."""
        if service_config.token is None or not _requires_local_token(request.url.path):
            return await call_next(request)
        authorization = request.headers.get("authorization", "")
        if not _valid_bearer_token(authorization, service_config.token):
            return JSONResponse(
                status_code=401,
                content={
                    "detail": {
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "valid bearer token required",
                        }
                    }
                },
            )
        return await call_next(request)

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


def _requires_local_token(path: str) -> bool:
    return path == "/api" or path.startswith("/api/")


def _valid_bearer_token(authorization: str, expected_token: str) -> bool:
    scheme, separator, provided_token = authorization.partition(" ")
    return (
        separator == " "
        and hmac.compare_digest(scheme.lower(), "bearer")
        and hmac.compare_digest(provided_token, expected_token)
    )
