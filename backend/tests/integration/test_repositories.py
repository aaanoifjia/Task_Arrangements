from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def test_repositories_persist_workflow_run_attempt_and_event(tmp_path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    workflow = WorkflowDefinition(
        id="workflow", name="Workflow", tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".")], edges=[]
    )
    repository.save_workflow_definition(workflow)
    assert repository.load_workflow("workflow") == workflow

    run_id = repository.create_workflow_run("workflow", {"workflow": "snapshot"})
    task_run_id = repository.create_task_runs(run_id, ["A"])[0]
    attempt_id = repository.create_attempt(task_run_id)
    repository.update_task_run_state(task_run_id, "RUNNING", "thread", "turn")
    repository.append_event("TURN_STARTED", {"turn": "turn"}, workflow_run_id=run_id, task_run_id=task_run_id, attempt_id=attempt_id)

    assert [row["id"] for row in repository.load_active_runs()] == [run_id]
    assert [row["id"] for row in repository.load_attempts(task_run_id)] == [attempt_id]
