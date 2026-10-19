"""WebSocket delivery of durable run snapshots and events."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from codex_flow.api.config import ServiceConfig
from codex_flow.api.lifespan import get_repositories
from codex_flow.application.event_stream import EventStream
from codex_flow.application.events import EventApplicationService

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/runs/{run_id}")
async def run_stream(websocket: WebSocket, run_id: str, after: str | None = None) -> None:
    await websocket.accept()
    repository = get_repositories(websocket.app)
    if repository.get_workflow_run(run_id) is None:
        await websocket.close(code=1008, reason="run not found")
        return
    config = getattr(websocket.app.state, "service_config", ServiceConfig.default())
    stream = EventStream(
        EventApplicationService(repository), config.event_poll_interval_seconds
    )
    try:
        async for message in stream.stream(run_id, after):
            await websocket.send_json({"kind": message.kind, "payload": message.payload})
    except WebSocketDisconnect:
        return
