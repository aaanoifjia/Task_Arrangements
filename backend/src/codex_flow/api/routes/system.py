"""Local process health and runtime status endpoints."""

from typing import Any

from fastapi import APIRouter, Request

from codex_flow.api.lifespan import get_connection

router = APIRouter(tags=["system"])


@router.get("/healthz")
async def health(request: Request) -> dict[str, str]:
    del request
    return {"status": "ok"}


@router.get("/api/system/status")
async def system_status(request: Request) -> dict[str, Any]:
    connection = get_connection(request.app)
    connection.execute("SELECT 1").fetchone()
    schema_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
    return {
        "service": "ok",
        "database": "reachable",
        "schema_version": schema_version,
        "active_runtime_count": request.app.state.runtime.active_count,
    }
