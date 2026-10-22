"""End-to-end local API lifecycle coverage for the release candidate."""

import asyncio
import threading
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig
from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexTurnRef, EventType


class ControlledFakeAdapter(FakeCodexAdapter):
    """Keep a local turn open long enough to exercise API controls."""

    def __init__(self) -> None:
        super().__init__()
        self.release = threading.Event()

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.calls.append("stream_turn")
        yield CodexEvent(
            event_type=EventType.TURN_STARTED,
            thread_id=turn.thread_id,
            turn_id=turn.turn_id,
        )
        await asyncio.to_thread(self.release.wait, 5)
        yield CodexEvent(
            event_type=EventType.TURN_COMPLETED,
            thread_id=turn.thread_id,
            turn_id=turn.turn_id,
        )


def _workflow_payload(cwd: Path) -> dict[str, object]:
    return {
        "id": "api-rc-workflow",
        "name": "API RC Workflow",
        "tasks": [
            {
                "id": "A",
                "name": "A",
                "prompt": "api smoke",
                "cwd": str(cwd),
            }
        ],
        "edges": [],
    }


def test_api_lifecycle_smoke_persists_control_attempt_and_events(tmp_path: Path) -> None:
    database = tmp_path / "api-rc.sqlite3"
    adapter = ControlledFakeAdapter()

    with TestClient(
        create_app(
            ServiceConfig(db_path=database, event_poll_interval_seconds=0),
            adapter=adapter,
        )
    ) as client:
        created = client.post("/api/workflows", json=_workflow_payload(tmp_path))
        assert created.status_code == 201
        assert created.json()["workflow"]["id"] == "api-rc-workflow"

        started = client.post("/api/workflows/api-rc-workflow/runs")
        assert started.status_code == 202
        run_id = started.json()["run_id"]

        paused = client.post(f"/api/runs/{run_id}/pause")
        assert paused.status_code == 200
        assert paused.json()["action"] == "PAUSE"
        assert paused.json()["accepted"] is True

        resumed = client.post(f"/api/runs/{run_id}/resume")
        assert resumed.status_code == 200
        assert resumed.json()["action"] == "RESUME"
        assert resumed.json()["accepted"] is True
        adapter.release.set()

        status = "PENDING"
        for _ in range(20):
            status = client.get(f"/api/runs/{run_id}").json()["status"]
            if status == "SUCCESS":
                break
        assert status == "SUCCESS"

        task = client.get(f"/api/runs/{run_id}/tasks/A")
        assert task.status_code == 200
        assert task.json()["status"] == "SUCCESS"
        attempts = client.get(f"/api/runs/{run_id}/tasks/A/attempts")
        assert attempts.status_code == 200
        assert len(attempts.json()) == 1
        assert attempts.json()[0]["status"] == "SUCCESS"

        event_types: list[str] = []
        snapshot_seen = False
        with client.websocket_connect(f"/ws/runs/{run_id}") as socket:
            for _ in range(5):
                message = socket.receive_json()
                if message["kind"] == "event":
                    event_types.append(message["payload"]["event_type"])
                if message["kind"] == "snapshot":
                    snapshot_seen = True
                    break

        assert event_types.count("MANUAL_ACTION_ACCEPTED") == 2
        assert snapshot_seen is True
        assert adapter.calls.count("create_thread") == 1
        assert adapter.calls.count("start_turn") == 1
