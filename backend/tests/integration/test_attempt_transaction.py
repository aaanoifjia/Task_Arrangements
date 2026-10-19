from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexExecutionConfig
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.storage.attempts import AttemptStarter
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


class ObservingAdapter(FakeCodexAdapter):
    def __init__(self, database_path: Path, task_run_id: str) -> None:
        super().__init__()
        self._database_path = database_path
        self._task_run_id = task_run_id
        self.observed_commit = False

    async def create_thread(self, config: CodexExecutionConfig):  # type: ignore[override]
        connection = open_database(self._database_path)
        task_status = connection.execute("SELECT status FROM task_runs WHERE id = ?", (self._task_run_id,)).fetchone()[0]
        attempts = connection.execute("SELECT count(*) FROM attempts WHERE task_run_id = ?", (self._task_run_id,)).fetchone()[0]
        self.observed_commit = task_status == "STARTING" and attempts == 1
        connection.close()
        return await super().create_thread(config)


async def test_attempt_is_committed_before_adapter_call(tmp_path: Path) -> None:
    database_path = tmp_path / "flow.sqlite3"
    repository = StorageRepositories(open_database(database_path))
    workflow = WorkflowDefinition(id="workflow", name="Workflow", tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".")], edges=[])
    repository.save_workflow_definition(workflow)
    run_id = repository.create_workflow_run("workflow", {})
    task_run_id = repository.create_task_runs(run_id, ["A"])[0]
    repository.update_task_run_state(task_run_id, "READY")
    adapter = ObservingAdapter(database_path, task_run_id)

    attempt_id, turn = await AttemptStarter(repository._connection, adapter).start(
        task_run_id, CodexExecutionConfig(cwd="."), "run"
    )

    assert adapter.observed_commit is True
    row = repository._connection.execute("SELECT thread_id, turn_id FROM attempts WHERE id = ?", (attempt_id,)).fetchone()
    assert tuple(row) == (turn.thread_id, turn.turn_id)


async def test_attempt_requires_ready_task_run(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = FakeCodexAdapter()

    with pytest.raises(ValueError, match="READY"):
        await AttemptStarter(repository._connection, adapter).start("missing", CodexExecutionConfig(cwd="."), "run")
    assert adapter.calls == []
