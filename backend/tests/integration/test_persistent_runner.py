from codex_flow.codex_adapter.fake import FakeCodexAdapter, FakeScenario
from codex_flow.domain.models import Edge, TaskDefinition, WorkflowDefinition
from codex_flow.runtime.runner import DurableRunner
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="A", cwd="."),
            TaskDefinition(id="B", name="B", prompt="B", cwd=".", dependencies=["A"]),
        ],
        edges=[Edge(source_task_id="A", target_task_id="B")],
    )


async def test_fresh_runner_persists_snapshot_attempts_and_successful_dependencies(tmp_path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = FakeCodexAdapter()

    run_id = await DurableRunner(repository, adapter).run(workflow())

    run = repository._connection.execute("SELECT snapshot_json, status FROM workflow_runs WHERE id = ?", (run_id,)).fetchone()
    task_rows = repository.load_task_runs(run_id)
    assert '"workflow"' in run["snapshot_json"]
    assert run["status"] == "SUCCESS"
    assert {row["task_id"]: row["status"] for row in task_rows} == {"A": "SUCCESS", "B": "SUCCESS"}
    assert all(len(repository.load_attempts(str(row["id"]))) == 1 for row in task_rows)
    assert adapter.calls == ["create_thread", "start_turn", "stream_turn"] * 2


async def test_failure_stays_closed_and_does_not_start_child(tmp_path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = FakeCodexAdapter(FakeScenario.FAILED)

    run_id = await DurableRunner(repository, adapter).run(workflow())

    assert {row["task_id"]: row["status"] for row in repository.load_task_runs(run_id)} == {
        "A": "FAILED",
        "B": "BLOCKED",
    }
    assert adapter.calls == ["create_thread", "start_turn", "stream_turn"]


async def test_restart_reconciles_active_run_without_duplicate_attempt_or_prompt(tmp_path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    repository.save_workflow_definition(workflow())
    run_id = repository.create_workflow_run("workflow", {"frozen": True})
    parent, child = repository.create_task_runs(run_id, ["A", "B"])
    repository.update_workflow_run_state(run_id, "RUNNING")
    repository.update_task_run_state(parent, "RUNNING", "persisted-thread", "persisted-turn")
    repository.update_task_run_state(child, "BLOCKED")
    repository.create_attempt(parent, "RUNNING")
    adapter = FakeCodexAdapter()

    assert await DurableRunner(repository, adapter).run(workflow()) == run_id
    assert adapter.calls == ["read_thread"]
    assert len(repository.load_attempts(parent)) == 1
    statuses = {row["task_id"]: row["status"] for row in repository.load_task_runs(run_id)}
    assert statuses == {"A": "NEEDS_ATTENTION", "B": "BLOCKED"}
