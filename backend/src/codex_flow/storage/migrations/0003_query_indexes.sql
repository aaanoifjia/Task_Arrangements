CREATE INDEX IF NOT EXISTS idx_workflow_runs_workflow_status
    ON workflow_runs(workflow_id, status);

CREATE INDEX IF NOT EXISTS idx_task_runs_run_status
    ON task_runs(workflow_run_id, status);

CREATE INDEX IF NOT EXISTS idx_attempts_task
    ON attempts(task_run_id);

CREATE INDEX IF NOT EXISTS idx_events_run_created_id
    ON events(workflow_run_id, created_at, id);
