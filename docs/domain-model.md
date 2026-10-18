# Codex Flow Domain Model Specification

This document is the canonical domain model for Scheduler, Persistence, API, and UI. It defines the entities and execution semantics shared by those components.

## Entities

### WorkflowDefinition

**Purpose**

An editable workflow template. It is not a real execution.

**Identity**

- `id`: stable identifier for the workflow definition.

**Core Fields**

- `id`
- `name`
- `description`
- `tasks`: collection of `TaskDefinition` objects.
- `edges`: collection of explicit `Edge` objects.
- `created_at`
- `updated_at`

**Lifecycle / Mutability**

Created, edited, and saved as a reusable template. It remains mutable until a run is started; starting a run creates an immutable workflow snapshot for that run.

**Relationships**

Owns task definitions and explicit dependency edges. A workflow definition may produce many independent `WorkflowRun` instances.

### TaskDefinition

**Purpose**

Defines one planned task in an editable workflow template.

**Identity**

- `id`: stable identifier within the workflow definition.

**Core Fields**

- `id`
- `name`
- `prompt`: the complete, user-prepared Codex Prompt. The system does not automatically rewrite the prompt.
- `cwd`
- `dependencies`: explicit dependency references, represented consistently with the workflow's `Edge` objects.
- `execution_mode`: exactly one of `NEW_THREAD` or `CONTINUE_THREAD`.
- `continue_from_task_id`: required when `execution_mode` is `CONTINUE_THREAD`; identifies the explicit upstream task whose Thread is continued.
- `model`
- `reasoning_effort`
- `sandbox`
- `approval_mode`
- `timeout_seconds`
- `retry_policy`

**Lifecycle / Mutability**

Editable while part of a `WorkflowDefinition`. Once copied into a `WorkflowRun` snapshot, its task configuration is immutable for that run.

**Relationships**

Belongs to a `WorkflowDefinition`; may be the source or target of explicit `Edge` objects. A task definition may produce task runs in multiple workflow runs.

`NEW_THREAD` means that when the task is Ready, the scheduler creates a new Codex Thread. `CONTINUE_THREAD` means that the scheduler continues the explicitly specified upstream task's Thread and must be used together with `continue_from_task_id`.

### Edge

**Purpose**

Expresses an explicit dependency between two task definitions.

**Identity**

- Stable edge identifier, or the unique pair of source and target task identifiers within a workflow definition.

**Core Fields**

- `source_task_id`
- `target_task_id`

`target_task_id` depends on `source_task_id`.

**Lifecycle / Mutability**

Editable as part of the workflow definition. Copied into the workflow run's immutable snapshot when execution starts.

**Relationships**

Connects two `TaskDefinition` objects. Edges are explicit; no LLM infers or changes task dependencies.

### WorkflowRun

**Purpose**

An independent execution instance created when the user clicks Run.

**Identity**

- Stable run identifier for this execution instance.

**Core Fields**

- Run identity and lifecycle timestamps/status.
- Immutable workflow snapshot containing the workflow's Prompt, task configuration, and dependencies as they existed when the run began.

**Lifecycle / Mutability**

Created at Run start and progressed by the deterministic scheduler. The execution snapshot is immutable after the run begins. Even if the original `WorkflowDefinition` is edited, the running instance's Prompt, Task Config, and Dependencies do not change.

**Relationships**

Derived from exactly one `WorkflowDefinition` at start, owns its immutable snapshot, and contains `TaskRun` objects. `WorkflowDefinition != WorkflowRun`.

### TaskRun

**Purpose**

Tracks execution state for one task within one workflow run.

**Identity**

- `id`: stable identifier for this task execution record.

**Core Fields**

- `id`
- `workflow_run_id`
- `task_definition_id`
- `status`
- `thread_id`: external Codex execution identity.
- `turn_id`: external Codex execution identity.
- `active_attempt_id`
- `started_at`
- `completed_at`
- `last_error`

**Lifecycle / Mutability**

Created from the immutable workflow snapshot and updated as the task moves through execution states. Its execution history is represented by separate attempts.

**Relationships**

Belongs to a `WorkflowRun`, refers to the snapshotted task definition, and owns one or more `Attempt` records. `thread_id` and `turn_id` identify execution in the external Codex system.

### Attempt

**Purpose**

Represents one actual execution attempt of a `TaskRun`.

**Identity**

- Stable identifier unique to the attempt.

**Core Fields**

- Attempt status and lifecycle timestamps.
- Execution result, error details, and relevant external execution references.

**Lifecycle / Mutability**

An attempt is created when execution starts and is retained as historical execution evidence. Each Retry creates a new `Attempt`; a previous attempt is never overwritten.

**Relationships**

Belongs to exactly one `TaskRun`. A task run can have multiple attempts:

```text
TaskRun
├── Attempt 1 FAILED
├── Attempt 2 FAILED
└── Attempt 3 SUCCESS
```

`TaskRun != Attempt`.

### Event

**Purpose**

An append-only audit / runtime event describing a workflow, task, attempt, or scheduler transition.

**Identity**

- `id`: unique event identifier.

**Core Fields**

- `id`
- `workflow_run_id`
- `task_run_id`
- `attempt_id`
- `event_type`
- `payload`
- `created_at`

**Lifecycle / Mutability**

Events are appended as facts occur. Historical events are never overwritten in place.

**Relationships**

May reference a workflow run, task run, and attempt according to the event scope; it provides the audit and runtime history for those entities.

## Invariants

- Definition != Run
- TaskRun != Attempt
- WorkflowRun uses an immutable execution snapshot
- Retry creates a new Attempt
- Task dependencies are explicit
- Scheduler does not use an LLM to infer dependencies
- Codex Desktop is not authoritative workflow state

