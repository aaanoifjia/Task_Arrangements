import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexThreadRef, CodexTurnRef, EventType
from codex_flow.domain.models import Edge, SandboxMode, TaskDefinition, WorkflowDefinition
from codex_flow.runtime.runner import DurableRunner
from codex_flow.scheduler.graph import topological_order
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


class TraceAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.started: list[str] = []
        self.completed: list[str] = []

    async def start_turn(self, thread: CodexThreadRef, prompt: str) -> CodexTurnRef:
        self.started.append(prompt)
        return await super().start_turn(thread, prompt)

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        await asyncio.sleep(0)
        self.completed.append(turn.turn_id)
        yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)


def large_workflow() -> WorkflowDefinition:
    tasks: list[TaskDefinition] = []
    edges: list[Edge] = []
    previous_tail: str | None = None
    for group in range(20):
        root = f"N{group:03d}-ROOT"
        left = f"N{group:03d}-LEFT"
        right = f"N{group:03d}-RIGHT"
        join = f"N{group:03d}-JOIN"
        tail = f"N{group:03d}-TAIL"
        group_nodes = [root, left, right, join, tail]
        dependencies: dict[str, list[str]] = {node: [] for node in group_nodes}
        if previous_tail is not None:
            edges.append(Edge(source_task_id=previous_tail, target_task_id=root))
            dependencies[root].append(previous_tail)
        for branch in (left, right):
            edges.append(Edge(source_task_id=root, target_task_id=branch))
            dependencies[branch].append(root)
        for branch in (left, right):
            edges.append(Edge(source_task_id=branch, target_task_id=join))
            dependencies[join].append(branch)
        edges.append(Edge(source_task_id=join, target_task_id=tail))
        dependencies[tail].append(join)
        tasks.extend(
            TaskDefinition(
                id=node,
                name=node,
                prompt=node,
                cwd=f"workspace-{group}",
                dependencies=dependencies[node],
                sandbox=SandboxMode.READ_ONLY,
            )
            for node in group_nodes
        )
        previous_tail = tail
    return WorkflowDefinition(id="large-dag", name="Large DAG", tasks=tasks, edges=edges)


async def execute_once(database: Path) -> tuple[list[str], list[str], dict[str, int]]:
    workflow = large_workflow()
    repository = StorageRepositories(open_database(database))
    adapter = TraceAdapter()
    run_id = await DurableRunner(repository, adapter, max_concurrency=2).run(workflow)
    rows = repository.load_task_runs(run_id)
    statuses = {str(row["task_id"]): str(row["status"]) for row in rows}
    attempt_counts = {
        str(row["task_id"]): len(repository.load_attempts(str(row["id"]))) for row in rows
    }
    assert all(statuses[task_id] == "SUCCESS" for task_id in topological_order(workflow))
    assert set(statuses.values()) == {"SUCCESS"}
    return adapter.started, adapter.completed, attempt_counts


@pytest.mark.asyncio
async def test_large_mixed_dag_is_deterministic_without_duplicates(tmp_path: Path) -> None:
    first = await execute_once(tmp_path / "first.sqlite3")
    second = await execute_once(tmp_path / "second.sqlite3")

    assert len(first[0]) == 100
    assert first[0] == second[0]
    assert first[1] == second[1]
    assert set(first[2].values()) == {1}
