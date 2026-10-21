from pathlib import Path

import pytest

from codex_flow.application.event_stream import EventStream
from codex_flow.application.events import EventApplicationService
from codex_flow.domain.models import WorkflowDefinition
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


class CountingEventService(EventApplicationService):
    def __init__(self, repository: StorageRepositories) -> None:
        super().__init__(repository)
        self.list_calls = 0

    def list_events(self, run_id: str, after_event_id: str | None = None):  # type: ignore[no-untyped-def]
        self.list_calls += 1
        return super().list_events(run_id, after_event_id)


@pytest.mark.asyncio
async def test_thousands_of_events_are_cursor_complete_and_batched(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    workflow = WorkflowDefinition(id="workflow", name="Workflow", tasks=[], edges=[])
    repository.save_workflow_definition(workflow)
    run_id = repository.create_workflow_run(workflow.id, workflow.model_dump())
    repository.update_workflow_run_state(run_id, "SUCCESS")

    expected_ids = [
        repository.append_event(
            "STRESS_EVENT", {"sequence": sequence}, workflow_run_id=run_id
        )
        for sequence in range(5_000)
    ]
    service = CountingEventService(repository)
    messages = [
        message
        async for message in EventStream(service, poll_interval_seconds=0, batch_size=127).stream(run_id)
    ]

    event_ids = [str(message.payload["id"]) for message in messages if message.kind == "event"]
    assert event_ids == expected_ids
    assert len(event_ids) == 5_000
    assert len(event_ids) == len(set(event_ids))
    assert service.list_calls == 40
