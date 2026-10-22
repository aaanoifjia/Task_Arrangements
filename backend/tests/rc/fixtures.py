"""Reusable deterministic fixtures for offline M11 release-candidate tests."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from types import TracebackType
from typing import Self

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter, FakeScenario
from codex_flow.domain.models import Edge, TaskDefinition, WorkflowDefinition
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def create_app_data_dir(root: Path, name: str = "app-data") -> Path:
    """Create and return an isolated application-data directory."""
    path = root / name
    path.mkdir(parents=True, exist_ok=False)
    return path


def make_linear_workflow(
    task_ids: Sequence[str] = ("A",),
    *,
    workflow_id: str = "rc-workflow",
    cwd: str = ".",
) -> WorkflowDefinition:
    """Build a fresh deterministic chain with one edge per adjacent task."""
    ids = tuple(task_ids)
    if not ids:
        raise ValueError("task_ids must not be empty")
    tasks = [
        TaskDefinition(
            id=task_id,
            name=task_id,
            prompt=f"prompt-{task_id}",
            cwd=cwd,
            dependencies=list(ids[:index]),
        )
        for index, task_id in enumerate(ids)
    ]
    edges = [Edge(source_task_id=source, target_task_id=target) for source, target in pairwise(ids)]
    return WorkflowDefinition(id=workflow_id, name=workflow_id, tasks=tasks, edges=edges)


def make_fake_adapter(scenario: FakeScenario = FakeScenario.SUCCESS) -> FakeCodexAdapter:
    """Return a fresh offline adapter with the requested deterministic scenario."""
    return FakeCodexAdapter(scenario)


@dataclass(frozen=True)
class PersistedRun:
    """Identifiers for a run persisted in an isolated SQLite database."""

    database_path: Path
    workflow: WorkflowDefinition
    run_id: str
    task_run_ids: tuple[str, ...]


def create_persisted_run(
    database_path: Path,
    workflow: WorkflowDefinition,
) -> PersistedRun:
    """Persist a workflow snapshot and its task runs, then close the connection."""
    connection = open_database(database_path)
    try:
        repository = StorageRepositories(connection)
        repository.save_workflow_definition(workflow)
        run_id = repository.create_workflow_run(workflow.id, workflow.model_dump(mode="json"))
        task_run_ids = tuple(repository.create_task_runs(run_id, [task.id for task in workflow.tasks]))
    finally:
        connection.close()
    return PersistedRun(database_path, workflow, run_id, task_run_ids)


@dataclass
class ProcessProbe:
    """Small process wrapper with explicit lifecycle operations and no polling sleep."""

    process: subprocess.Popen[str]

    @property
    def returncode(self) -> int | None:
        return self.process.returncode

    def wait(self, timeout: float = 5.0) -> int:
        return self.process.wait(timeout=timeout)

    def terminate(self, timeout: float = 5.0) -> int:
        if self.process.poll() is None:
            self.process.terminate()
        return self.wait(timeout)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self.process.poll() is None:
            self.terminate()


def launch_process_probe(
    command: Sequence[str] | None = None,
    *,
    cwd: Path | None = None,
) -> ProcessProbe:
    """Launch a local process probe; callers control completion or termination."""
    selected_command = list(command or (sys.executable, "-c", "print('probe-ready')"))
    return ProcessProbe(
        subprocess.Popen(
            selected_command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    )


@pytest.fixture
def app_data_dir(tmp_path: Path) -> Path:
    return create_app_data_dir(tmp_path)


@pytest.fixture
def fake_adapter() -> FakeCodexAdapter:
    return make_fake_adapter()


@pytest.fixture
def persisted_run(app_data_dir: Path) -> PersistedRun:
    workflow = make_linear_workflow(("A", "B"), cwd=str(app_data_dir))
    return create_persisted_run(app_data_dir / "flow.sqlite3", workflow)
