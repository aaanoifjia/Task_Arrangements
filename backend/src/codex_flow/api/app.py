"""Explicit FastAPI application construction."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from codex_flow.api.config import ServiceConfig
from codex_flow.api.lifespan import lifespan


def create_app(config: ServiceConfig | None = None) -> FastAPI:
    """Construct the local API without opening resources or starting a server."""
    service_config = config or ServiceConfig.default()

    @asynccontextmanager
    async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with lifespan(app, service_config):
            yield

    app = FastAPI(title="Codex Flow Local API", version="0.1.0", lifespan=app_lifespan)
    app.state.service_config = service_config
    return app
