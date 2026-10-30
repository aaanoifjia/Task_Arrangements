import pytest

from codex_flow.codex_adapter.sdk import SdkCodexAdapter
from codex_flow.domain.models import Edge, TaskDefinition, WorkflowDefinition
from codex_flow.runtime.runner import DurableRunner
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


@pytest.mark.live_codex
async def test_real_durable_runner_starts_dependent_task_automatically(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    workflow = WorkflowDefinition(
        id="live-durable-linear",
        name="Live durable linear",
        tasks=[
            TaskDefinition(
                id="A",
                name="Create A",
                prompt=(
                    "Run this exact command and do not substitute another command: "
                    "python -c \"from pathlib import Path; Path('task_a.txt').write_bytes(b'TASK_A_DONE')\". "
                    "This must produce exactly those bytes with no trailing newline. Stop."
                ),
                cwd=str(workspace),
            ),
            TaskDefinition(
                id="B",
                name="Create B",
                prompt=(
                    "Read task_a.txt and verify it contains exactly TASK_A_DONE. "
                    "Then run this exact command and do not substitute another command: "
                    "python -c \"from pathlib import Path; Path('task_b.txt').write_bytes(b'TASK_B_DONE')\". "
                    "This must produce exactly those bytes with no trailing newline. Stop."
                ),
                cwd=str(workspace),
                dependencies=["A"],
            ),
        ],
        edges=[Edge(source_task_id="A", target_task_id="B")],
    )
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = SdkCodexAdapter()
    try:
        run_id = await DurableRunner(repository, adapter).run(workflow)
        assert repository.get_workflow_run(run_id)["status"] == "SUCCESS"
        assert {row["task_id"]: row["status"] for row in repository.load_task_runs(run_id)} == {
            "A": "SUCCESS",
            "B": "SUCCESS",
        }
        assert (workspace / "task_a.txt").read_text(encoding="utf-8") == "TASK_A_DONE"
        assert (workspace / "task_b.txt").read_text(encoding="utf-8") == "TASK_B_DONE"
    finally:
        await adapter.close()
