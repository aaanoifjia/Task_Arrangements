PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE workflows (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    definition_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE tasks (
    workflow_id TEXT NOT NULL REFERENCES workflows(id),
    id TEXT NOT NULL,
    definition_json TEXT NOT NULL,
    PRIMARY KEY (workflow_id, id)
);

CREATE TABLE edges (
    workflow_id TEXT NOT NULL REFERENCES workflows(id),
    source_task_id TEXT NOT NULL,
    target_task_id TEXT NOT NULL,
    PRIMARY KEY (workflow_id, source_task_id, target_task_id),
    FOREIGN KEY (workflow_id, source_task_id) REFERENCES tasks(workflow_id, id),
    FOREIGN KEY (workflow_id, target_task_id) REFERENCES tasks(workflow_id, id)
);

CREATE TABLE workflow_runs (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflows(id),
    snapshot_json TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE task_runs (
    id TEXT PRIMARY KEY,
    workflow_run_id TEXT NOT NULL REFERENCES workflow_runs(id),
    task_id TEXT NOT NULL,
    status TEXT NOT NULL,
    thread_id TEXT,
    turn_id TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE attempts (
    id TEXT PRIMARY KEY,
    task_run_id TEXT NOT NULL REFERENCES task_runs(id),
    status TEXT NOT NULL,
    thread_id TEXT,
    turn_id TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE events (
    id TEXT PRIMARY KEY,
    workflow_run_id TEXT REFERENCES workflow_runs(id),
    task_run_id TEXT REFERENCES task_runs(id),
    attempt_id TEXT REFERENCES attempts(id),
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
