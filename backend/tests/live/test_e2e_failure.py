import pytest

from codex_flow.codex_adapter.sdk import SdkCodexAdapter
from codex_flow.domain.models import Edge, TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.scheduler.engine import AsyncScheduler


@pytest.mark.live_codex
async def test_real_failure_does_not_create_downstream_thread(tmp_path) -> None:
    adapter = SdkCodexAdapter()
    workflow = WorkflowDefinition(
        id="real-failure",
        name="Real failure propagation",
        tasks=[
            TaskDefinition(
                id="parent",
                name="Parent",
                prompt="Run a command that exits with status 1, then stop.",
                cwd=str(tmp_path),
            ),
            TaskDefinition(
                id="child",
                name="Child",
                prompt="Create child.txt containing exactly CHILD_DONE and no newline. Stop.",
                cwd=str(tmp_path),
                dependencies=["parent"],
            ),
        ],
        edges=[Edge(source_task_id="parent", target_task_id="child")],
    )
    try:
        scheduler = AsyncScheduler(workflow, adapter)
        assert await scheduler.run_until_idle() == {
            "parent": TaskStatus.FAILED,
            "child": TaskStatus.BLOCKED,
        }
        assert len(adapter._threads) == 1
        assert not (tmp_path / "child.txt").exists()
    finally:
        await adapter.close()
