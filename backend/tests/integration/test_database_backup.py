import sqlite3
from pathlib import Path

from codex_flow.application.backup import create_database_backup
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="backup-workflow",
        name="Backup workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="safe", cwd=".")],
        edges=[],
    )


def test_online_backup_contains_consistent_schema_workflow_and_run_snapshot(tmp_path: Path) -> None:
    source_path = tmp_path / "source.sqlite3"
    backup_path = tmp_path / "backups" / "copy.sqlite3"
    source = open_database(source_path)
    repositories = StorageRepositories(source)
    definition = workflow()
    repositories.save_workflow_definition(definition)
    run_id = repositories.create_workflow_run(definition.id, definition.model_dump(mode="json"))
    repositories.create_task_runs(run_id, ["A"])

    result = create_database_backup(source, backup_path)

    assert result == backup_path
    assert source.execute("SELECT COUNT(*) FROM workflows").fetchone()[0] == 1
    source.close()
    copied = sqlite3.connect(backup_path)
    try:
        assert copied.execute("PRAGMA user_version").fetchone()[0] == 3
        assert copied.execute("SELECT id, name FROM workflows").fetchone() == ("backup-workflow", "Backup workflow")
        assert copied.execute("SELECT workflow_id, status FROM workflow_runs").fetchone() == (definition.id, "PENDING")
        assert copied.execute("SELECT task_id, status FROM task_runs").fetchone() == ("A", "PENDING")
    finally:
        copied.close()
