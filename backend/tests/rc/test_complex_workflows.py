"""Deterministic 20-node mixed DAG release-candidate scenario."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexThreadRef, CodexTurnRef, EventType
from codex_flow.domain.models import Edge, ExecutionMode, TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.runtime.manager import RuntimeManager
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


def continuation_workflow() -> WorkflowDefinition:
    dependencies = {
        "A": (),
        "B": ("A",),
        "C": ("A",),
        "D": ("B",),
        "E": ("C",),
        "F": ("D", "E"),
        "G": ("A",),
        "H": ("F", "G"),
        "I": ("H",),
        "J": ("I", "C"),
    }
    continuation_sources = {"B": "A", "D": "B", "I": "H"}
    tasks = [
        TaskDefinition(
            id=task_id,
            name=task_id,
            prompt=task_id,
            cwd=f"continuation-{task_id}",
            dependencies=list(task_dependencies),
            execution_mode=(
                ExecutionMode.CONTINUE_THREAD
                if task_id in continuation_sources
                else ExecutionMode.NEW_THREAD
            ),
            continue_from_task_id=continuation_sources.get(task_id),
        )
        for task_id, task_dependencies in dependencies.items()
    ]
    edges = [
        Edge(source_task_id=source, target_task_id=target)
        for target, task_dependencies in dependencies.items()
        for source in task_dependencies
    ]
    return WorkflowDefinition(id="continuation-chain-workflow", name="Continuation Chain", tasks=tasks, edges=edges)


class FailureRecoveryAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.started_prompts: list[str] = []
        self._failed_turns: set[str] = set()

    async def start_turn(self, thread: CodexThreadRef, prompt: str) -> CodexTurnRef:
        self.started_prompts.append(prompt)
        turn = await super().start_turn(thread, prompt)
        if prompt == "B" and not self._failed_turns:
            self._failed_turns.add(turn.turn_id)
        return turn

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.calls.append("stream_turn")
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        terminal = EventType.TURN_FAILED if turn.turn_id in self._failed_turns else EventType.TURN_COMPLETED
        yield CodexEvent(event_type=terminal, thread_id=turn.thread_id, turn_id=turn.turn_id)


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


@pytest.mark.asyncio
async def test_failure_retry_pause_resume_and_skip_preserve_dag_states(tmp_path: Path) -> None:
    workflow = WorkflowDefinition(
        id="failure-recovery-workflow",
        name="Failure Recovery Workflow",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="A", cwd="."),
            TaskDefinition(id="B", name="B", prompt="B", cwd=".", dependencies=["A"]),
            TaskDefinition(id="C", name="C", prompt="C", cwd=".", dependencies=["B"]),
            TaskDefinition(id="D", name="D", prompt="D", cwd=".",),
            TaskDefinition(id="E", name="E", prompt="E", cwd=".", dependencies=["D"]),
        ],
        edges=[
            Edge(source_task_id="A", target_task_id="B"),
            Edge(source_task_id="B", target_task_id="C"),
            Edge(source_task_id="D", target_task_id="E"),
        ],
    )
    connection = open_database(tmp_path / "failure-recovery.sqlite3")
    try:
        repository = StorageRepositories(connection)
        adapter = FailureRecoveryAdapter()
        manager = RuntimeManager(repository, adapter)
        repository.save_workflow_definition(workflow)
        run_id = repository.create_workflow_run(workflow.id, workflow.model_dump(mode="json"))
        task_ids = repository.create_task_runs(run_id, ["A", "B", "C", "D", "E"])
        by_task_id = dict(zip(("A", "B", "C", "D", "E"), task_ids, strict=True))
        repository.update_workflow_run_state(run_id, TaskStatus.RUNNING.value)
        repository.update_task_run_state(by_task_id["A"], TaskStatus.PENDING.value)
        repository.update_task_run_state(by_task_id["B"], TaskStatus.BLOCKED.value)
        repository.update_task_run_state(by_task_id["C"], TaskStatus.BLOCKED.value)
        repository.update_task_run_state(by_task_id["D"], TaskStatus.READY.value)
        repository.update_task_run_state(by_task_id["E"], TaskStatus.BLOCKED.value)
        manager.restore_workflow(run_id, workflow)

        paused = await manager.pause(run_id)
        assert paused.accepted
        assert adapter.calls == []
        skipped = await manager.skip(run_id, by_task_id["D"])
        assert skipped.accepted
        assert repository.get_task_run(by_task_id["E"])["status"] == TaskStatus.BLOCKED.value
        resumed = await manager.resume(run_id)
        await manager.wait(run_id)

        assert resumed.accepted
        assert repository.get_task_run(by_task_id["A"])["status"] == TaskStatus.SUCCESS.value
        assert repository.get_task_run(by_task_id["B"])["status"] == TaskStatus.FAILED.value
        assert repository.get_task_run(by_task_id["C"])["status"] == TaskStatus.BLOCKED.value
        assert repository.get_task_run(by_task_id["D"])["status"] == TaskStatus.SKIPPED.value
        assert repository.get_task_run(by_task_id["E"])["status"] == TaskStatus.BLOCKED.value

        manager.restore_workflow(run_id, workflow)
        retried = await manager.retry(run_id, by_task_id["B"])
        await manager.wait(run_id)

        assert retried.accepted
        assert repository.get_task_run(by_task_id["B"])["status"] == TaskStatus.SUCCESS.value
        assert repository.get_task_run(by_task_id["C"])["status"] == TaskStatus.SUCCESS.value
        assert repository.get_task_run(by_task_id["E"])["status"] == TaskStatus.BLOCKED.value
        assert repository.get_workflow_run(run_id)["status"] == TaskStatus.FAILED.value
        assert len(repository.load_attempts(by_task_id["B"])) == 2
        assert adapter.started_prompts == ["A", "B", "B", "C"]
        audit_types = [event["event_type"] for event in repository.load_events_for_run(run_id)]
        assert audit_types.count("MANUAL_ACTION_ACCEPTED") == 4
        assert "RETRY_REQUESTED" in audit_types
    finally:
        connection.close()


@pytest.mark.asyncio
async def test_continuation_chain_reuses_only_explicit_source_threads(tmp_path: Path) -> None:
    workflow = continuation_workflow()
    dependencies = {
        "A": (),
        "B": ("A",),
        "C": ("A",),
        "D": ("B",),
        "E": ("C",),
        "F": ("D", "E"),
        "G": ("A",),
        "H": ("F", "G"),
        "I": ("H",),
        "J": ("I", "C"),
    }
    connection = open_database(tmp_path / "continuation-chain.sqlite3")
    try:
        repository = StorageRepositories(connection)
        adapter = RecordingAdapter()
        run_id = await DurableRunner(repository, adapter, max_concurrency=3).run(workflow)
        rows = {str(row["task_id"]): row for row in repository.load_task_runs(run_id)}
        order = {task_id: index for index, task_id in enumerate(adapter.started_prompts)}

        assert all(row["status"] == TaskStatus.SUCCESS.value for row in rows.values())
        assert len(adapter.started_prompts) == 10
        assert len(set(adapter.started_prompts)) == 10
        assert all(order[parent] < order[task_id] for task_id, parents in dependencies.items() for parent in parents)
        assert adapter.resumed_threads == [rows["A"]["thread_id"], rows["B"]["thread_id"], rows["H"]["thread_id"]]
        assert rows["B"]["thread_id"] == rows["A"]["thread_id"]
        assert rows["D"]["thread_id"] == rows["B"]["thread_id"]
        assert rows["I"]["thread_id"] == rows["H"]["thread_id"]
        new_thread_tasks = ("A", "C", "E", "F", "G", "H", "J")
        assert len({rows[task_id]["thread_id"] for task_id in new_thread_tasks}) == 7
        assert all(len(repository.load_attempts(str(row["id"]))) == 1 for row in rows.values())
    finally:
        connection.close()
