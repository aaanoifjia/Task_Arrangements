"""Deterministic 20-node mixed DAG release-candidate scenario."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexThreadRef, CodexTurnRef, EventType
from codex_flow.domain.models import Edge, ExecutionMode, TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.runtime.runner import DurableRunner
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories

DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "A": (),
    "B": ("A",),
    "C": ("A",),
    "D": ("B",),
    "E": ("C",),
    "F": ("B", "C"),
    "G": ("D", "E"),
    "H": ("F", "G"),
    "I": (),
    "J": (),
    "K": ("I",),
    "L": ("J",),
    "M": ("K", "L"),
    "N": ("A",),
    "O": ("N",),
    "P": ("O", "F"),
    "Q": ("M", "H"),
    "R": ("P", "Q"),
    "S": (),
    "T": ("S",),
}
CONTINUATIONS = {"N": "A", "O": "N"}


def mixed_workflow() -> WorkflowDefinition:
    tasks = [
        TaskDefinition(
            id=task_id,
            name=task_id,
            prompt=f"prompt-{task_id}",
            cwd=f"workspace-{task_id}",
            dependencies=list(dependencies),
            execution_mode=(
                ExecutionMode.CONTINUE_THREAD if task_id in CONTINUATIONS else ExecutionMode.NEW_THREAD
            ),
            continue_from_task_id=CONTINUATIONS.get(task_id),
        )
        for task_id, dependencies in DEPENDENCIES.items()
    ]
    edges = [
        Edge(source_task_id=source, target_task_id=target)
        for target, dependencies in DEPENDENCIES.items()
        for source in dependencies
    ]
    return WorkflowDefinition(
        id="mixed-20-workflow",
        name="Mixed 20 Node Workflow",
        tasks=tasks,
        edges=edges,
    )


class RecordingAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.started_prompts: list[str] = []
        self.resumed_threads: list[str] = []

    async def resume_thread(self, thread: CodexThreadRef) -> CodexThreadRef:
        self.resumed_threads.append(thread.thread_id)
        return await super().resume_thread(thread)

    async def start_turn(self, thread: CodexThreadRef, prompt: str) -> CodexTurnRef:
        self.started_prompts.append(prompt)
        return await super().start_turn(thread, prompt)

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.calls.append("stream_turn")
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)


@pytest.mark.asyncio
async def test_twenty_node_mixed_dag_is_deterministic_and_single_execution(tmp_path: Path) -> None:
    workflow = mixed_workflow()
    connection = open_database(tmp_path / "mixed-20.sqlite3")
    try:
        repository = StorageRepositories(connection)
        adapter = RecordingAdapter()
        run_id = await DurableRunner(repository, adapter, max_concurrency=4).run(workflow)
        rows = repository.load_task_runs(run_id)
        by_task = {str(row["task_id"]): row for row in rows}
        start_order = [prompt.removeprefix("prompt-") for prompt in adapter.started_prompts]
        start_index = {task_id: index for index, task_id in enumerate(start_order)}

        assert len(rows) == 20
        assert set(by_task) == set(DEPENDENCIES)
        assert all(row["status"] == TaskStatus.SUCCESS.value for row in rows)
        assert all(len(repository.load_attempts(str(row["id"]))) == 1 for row in rows)
        assert len(adapter.started_prompts) == 20
        assert len(set(adapter.started_prompts)) == 20
        for task_id, dependencies in DEPENDENCIES.items():
            assert all(start_index[parent] < start_index[task_id] for parent in dependencies)

        assert len(adapter.resumed_threads) == 2
        assert by_task["N"]["thread_id"] == by_task["A"]["thread_id"]
        assert by_task["O"]["thread_id"] == by_task["N"]["thread_id"]
        new_thread_ids = {
            str(by_task[task_id]["thread_id"])
            for task_id in DEPENDENCIES
            if task_id not in CONTINUATIONS
        }
        assert len(new_thread_ids) == 18
        assert by_task["A"]["thread_id"] not in {
            by_task[task_id]["thread_id"] for task_id in ("B", "C", "I", "J", "S")
        }
    finally:
        connection.close()
