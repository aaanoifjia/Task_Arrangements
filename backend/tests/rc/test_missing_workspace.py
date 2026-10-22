"""Fail-visible behavior for a workflow whose configured cwd disappeared."""

from __future__ import annotations

from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexExecutionConfig
from codex_flow.domain.models import Edge, TaskDefinition, WorkflowDefinition
from codex_flow.runtime.runner import DurableRunner
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


class CwdCheckingAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.observed_cwd: str | None = None

    async def create_thread(self, config: CodexExecutionConfig):
        self.observed_cwd = config.cwd
        if not Path(config.cwd).is_dir():
            raise FileNotFoundError(config.cwd)
        return await super().create_thread(config)


@pytest.mark.asyncio
async def test_removed_workspace_fails_visible_without_fallback_or_child_start(
    tmp_path: Path,
) -> None:
    removed_workspace = tmp_path / "removed workspace"
    removed_workspace.mkdir()
    removed_workspace.rmdir()
    workflow = WorkflowDefinition(
        id="missing-workspace-workflow",
        name="Missing Workspace Workflow",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="A", cwd=str(removed_workspace)),
            TaskDefinition(
                id="B", name="B", prompt="B", cwd=str(tmp_path), dependencies=["A"]
            ),
        ],
        edges=[Edge(source_task_id="A", target_task_id="B")],
    )
    connection = open_database(tmp_path / "flow.sqlite3")
    try:
        repository = StorageRepositories(connection)
        adapter = CwdCheckingAdapter()
        runner = DurableRunner(repository, adapter)
        run_id = runner.prepare_run(workflow)

        with pytest.raises(FileNotFoundError, match="removed workspace"):
            await runner.execute_run(run_id, workflow)

        rows = {str(row["task_id"]): row for row in repository.load_task_runs(run_id)}
        assert adapter.observed_cwd == str(removed_workspace)
        assert rows["A"]["status"] == "STARTING"
        assert rows["B"]["status"] == "BLOCKED"
        assert adapter.calls == []
    finally:
        connection.close()
