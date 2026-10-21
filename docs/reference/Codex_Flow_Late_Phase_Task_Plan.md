# Codex Flow — Late Phase Task Plan (M8–M10)

This file is the authoritative concrete task plan after M7. It targets a long autonomous execution window (roughly 7–9 hours on the current project velocity) while preserving small durable checkpoints.

Global rules:

- Follow AGENTS.md and .codex/AUTO_EXECUTION.md.
- SQLite remains authoritative durable state.
- No master LLM control plane.
- No private Codex Desktop DB/LevelDB/renderer IPC access.
- Codex integration stays behind CodexAdapter.
- Do not silently broaden TaskStatus or workflow semantics.
- Automatic pull/push behavior follows repository policy.
- M8–M10 tasks use FakeCodexAdapter for automated tests unless a task explicitly states otherwise.
- Do not require user/manual GUI interaction until M10-REPORT-036 has completed.
- If a task discovers a defect in its own milestone, the milestone integration/gate tasks have bounded repair ownership; do not weaken tests.
- A real missing toolchain/credential/external dependency remains a genuine blocker.

# M8 — Human-in-the-loop & Reliability

## Goal

Turn the already-tested scheduler manual operations into durable runtime behavior, public REST controls, auditable events, and usable UI controls without moving scheduling decisions into the frontend.

## Frozen boundaries

- Pause/Resume control workflow progression only; pause does not add a TaskRun state.
- Retry always creates a new Attempt and preserves prior attempts.
- Cancel/Skip/Mark Success obey the frozen state machine.
- All manual overrides are auditable and durable.
- Frontend never infers legality beyond server-advertised/durable state.
- Browser notifications are best-effort presentation only; workflow correctness never depends on them.

## Deterministic Task Order

```text
M8-CONTROL-001
↓
M8-CONTROL-002
↓
M8-CONTROL-003
↓
M8-CONTROL-004
↓
M8-CONTROL-005
↓
M8-CONTROL-006
↓
M8-CONTROL-007
↓
M8-CONTROL-008
↓
M8-CONTROL-009
↓
M8-CONTROL-010
↓
M8-CONTROL-011
↓
M8-CONTROL-012
↓
M8-CONTROL-013
↓
M8-CONTROL-014
↓
M8-CONTROL-015
↓
M8-CONTROL-016
↓
M8-CONTROL-017
↓
M8-CONTROL-018
↓
M8-CONTROL-019
↓
M8-CONTROL-020
↓
M8-CONTROL-021
↓
M8-CONTROL-022
↓
M8-CONTROL-023
↓
M8-CONTROL-024
↓
M8-CONTROL-025
↓
M8-CONTROL-026
↓
M8-CONTROL-027
↓
M8-CONTROL-028
↓
M8-CONTROL-029
↓
M8-CONTROL-030
↓
M8-UI-031A
↓
M8-UI-031
↓
M8-UI-032A
↓
M8-UI-032
↓
M8-UI-033
↓
M8-UI-034
↓
M8-UI-035
↓
M8-UI-036
↓
M8-UI-037
↓
M8-UI-038
↓
M8-UI-039
↓
M8-UI-040
↓
M8-UI-041
↓
M8-INTEGRATE-042
↓
M8-GATE-043
↓
M8-REPORT-044
```

Execute exactly in this order unless a genuine blocker occurs. Completion of an individual task is not a stop condition.

---

## M8-CONTROL-001 — Durable Control Contract

### Dependencies

`M7-REPORT-058`

### Owned Files

```text
backend/src/codex_flow/application/control_contract.py
backend/tests/unit/test_control_contract.py
```

### Implementation

Define SDK-independent durable control commands/results for pause, resume, retry, cancel, skip, mark-success. Preserve frozen TaskStatus rules; Retry is a special new-attempt operation, not a terminal-state transition.

### Acceptance

Command/result validation matrix passes; no Codex SDK imports.

---

## M8-CONTROL-002 — Pause Persistence Migration

### Dependencies

`M8-CONTROL-001`

### Owned Files

```text
backend/src/codex_flow/storage/migrations/0002_run_controls.sql
backend/src/codex_flow/storage/schema.py
backend/tests/integration/test_migration_0002.py
```

### Implementation

Add durable workflow-run pause flag/state metadata without adding TaskRun states. Migration must upgrade v1 databases and be idempotent.

### Acceptance

Fresh DB and v1 upgrade tests pass; M4 migration regression passes.

---

## M8-CONTROL-003 — Control Repository Primitives

### Dependencies

`M8-CONTROL-002`

### Owned Files

```text
backend/src/codex_flow/storage/repositories.py
backend/tests/integration/test_control_repository.py
```

### Implementation

Add transactional run pause read/write helpers and compare-state task updates needed by manual control. No route code may issue SQL.

### Acceptance

Repository control tests pass; stale-state compare update fails closed.

---

## M8-CONTROL-004 — Manual Action Audit Events

### Dependencies

`M8-CONTROL-003`

### Owned Files

```text
backend/src/codex_flow/storage/repositories.py
backend/src/codex_flow/application/control_contract.py
backend/tests/integration/test_manual_action_audit.py
```

### Implementation

Persist append-only audit events for every accepted/rejected manual action with run/task/action/previous/target metadata and no credentials.

### Acceptance

Accepted and rejected action audit tests pass with deterministic payloads.

---

## M8-CONTROL-005 — Transactional Retry Reset

### Dependencies

`M8-CONTROL-004`

### Owned Files

```text
backend/src/codex_flow/storage/repositories.py
backend/tests/integration/test_retry_reset.py
```

### Implementation

Implement explicit retry reset for FAILED/INTERRUPTED/NEEDS_ATTENTION TaskRun: preserve prior attempts, clear current external refs, return task to PENDING under one transaction, record RETRY_REQUESTED.

### Acceptance

Retry reset creates no Attempt itself, preserves history, rejects invalid source states.

---

## M8-CONTROL-006 — Runtime Active Turn Registry

### Dependencies

`M8-CONTROL-005`

### Owned Files

```text
backend/src/codex_flow/runtime/runner.py
backend/src/codex_flow/runtime/manager.py
backend/tests/integration/test_active_turn_registry.py
```

### Implementation

Track currently executing CodexTurnRef by task-run in process memory only so explicit cancel can interrupt active work. Durable DB remains authoritative.

### Acceptance

Registry appears only while turn is active and is cleaned on every terminal/error path.

---

## M8-CONTROL-007 — Pause Scheduling Checkpoint

### Dependencies

`M8-CONTROL-006`

### Owned Files

```text
backend/src/codex_flow/runtime/runner.py
backend/tests/integration/test_runner_pause_checkpoint.py
```

### Implementation

Before releasing each newly-ready task, consult durable run pause state. Pause never interrupts a task already running; it only prevents new starts.

### Acceptance

Pause between A and B prevents B external start while A may finish.

---

## M8-CONTROL-008 — Terminal-vs-Control Race Guard

### Dependencies

`M8-CONTROL-007`

### Owned Files

```text
backend/src/codex_flow/runtime/runner.py
backend/src/codex_flow/storage/repositories.py
backend/tests/integration/test_control_terminal_race.py
```

### Implementation

Persist terminal Codex result only when TaskRun is still in an execution-compatible state. A user CANCELLED task must never be overwritten later by SUCCESS/FAILED stream completion.

### Acceptance

Cancel-versus-terminal race matrix passes fail-closed.

---

## M8-CONTROL-009 — Runtime Pause Operation

### Dependencies

`M8-CONTROL-008`

### Owned Files

```text
backend/src/codex_flow/runtime/manager.py
backend/tests/integration/test_runtime_pause.py
```

### Implementation

Expose pause(run_id): validate active durable run, set pause atomically, append audit event, leave current turn untouched.

### Acceptance

Paused run stops releasing new tasks and reports pause state durably.

---

## M8-CONTROL-010 — Runtime Resume Operation

### Dependencies

`M8-CONTROL-009`

### Owned Files

```text
backend/src/codex_flow/runtime/manager.py
backend/tests/integration/test_runtime_resume.py
```

### Implementation

Expose resume(run_id): clear durable pause, re-enter execution for an unfinished run exactly once, and avoid duplicate background runners.

### Acceptance

Resume continues pending/ready work and duplicate resume is rejected or no-op deterministically.

---

## M8-CONTROL-011 — Runtime Retry Operation

### Dependencies

`M8-CONTROL-010`

### Owned Files

```text
backend/src/codex_flow/runtime/manager.py
backend/src/codex_flow/runtime/runner.py
backend/tests/integration/test_runtime_retry.py
```

### Implementation

Expose retry(run_id, task_run_id): use transactional retry reset, reopen workflow-run execution, create a fresh Attempt only when scheduler starts the task.

### Acceptance

Failed parent retry can execute again without overwriting old Attempt.

---

## M8-CONTROL-012 — Cancel Queued Task

### Dependencies

`M8-CONTROL-011`

### Owned Files

```text
backend/src/codex_flow/runtime/manager.py
backend/tests/integration/test_cancel_queued.py
```

### Implementation

Cancel PENDING/BLOCKED/READY task with canonical USER_ACTION transition and audit event. Do not create external thread/turn.

### Acceptance

Queued cancellation produces CANCELLED and no adapter execution.

---

## M8-CONTROL-013 — Cancel Running Task

### Dependencies

`M8-CONTROL-012`

### Owned Files

```text
backend/src/codex_flow/runtime/manager.py
backend/src/codex_flow/runtime/runner.py
backend/tests/integration/test_cancel_running.py
```

### Implementation

For STARTING/RUNNING task, request adapter interrupt when a turn exists, then persist explicit CANCELLED safely. Unknown external state fails closed.

### Acceptance

Running cancel calls interrupt at most once and terminal stream cannot overwrite CANCELLED.

---

## M8-CONTROL-014 — Skip Task Operation

### Dependencies

`M8-CONTROL-013`

### Owned Files

```text
backend/src/codex_flow/runtime/manager.py
backend/tests/integration/test_skip_task.py
```

### Implementation

Support SKIP only where frozen state machine permits it. Skipped dependency must not release children because READY requires parent SUCCESS.

### Acceptance

Skip legality and downstream blocking tests pass.

---

## M8-CONTROL-015 — Mark Success Operation

### Dependencies

`M8-CONTROL-014`

### Owned Files

```text
backend/src/codex_flow/runtime/manager.py
backend/tests/integration/test_mark_success.py
```

### Implementation

Support explicit Mark Success only where frozen state machine permits it, append audit evidence, then re-evaluate downstream readiness.

### Acceptance

READY -> SUCCESS manual override releases valid children and is auditable.

---

## M8-CONTROL-016 — Needs-Attention Controls

### Dependencies

`M8-CONTROL-015`

### Owned Files

```text
backend/src/codex_flow/runtime/manager.py
backend/tests/integration/test_attention_controls.py
```

### Implementation

Define deterministic actions from NEEDS_ATTENTION: Retry via retry reset and Cancel via user action; do not invent implicit success.

### Acceptance

Attention action matrix passes; no silent downstream release.

---

## M8-CONTROL-017 — Control Application Service

### Dependencies

`M8-CONTROL-016`

### Owned Files

```text
backend/src/codex_flow/application/controls.py
backend/tests/unit/test_control_service.py
```

### Implementation

Add application service translating not-found/conflict/invalid-action runtime errors into stable domain errors. Routes must not call RuntimeManager methods directly after this layer exists.

### Acceptance

Service unit matrix passes for every action.

---

## M8-CONTROL-018 — Control API Schemas

### Dependencies

`M8-CONTROL-017`

### Owned Files

```text
backend/src/codex_flow/api/schemas.py
backend/tests/api/test_control_schemas.py
```

### Implementation

Add ManualActionResponse and durable run control state to public DTOs without SDK objects.

### Acceptance

OpenAPI/schema serialization tests pass.

---

## M8-CONTROL-019 — Pause REST Endpoint

### Dependencies

`M8-CONTROL-018`

### Owned Files

```text
backend/src/codex_flow/api/routes/controls.py
backend/src/codex_flow/api/app.py
backend/tests/api/test_pause_route.py
```

### Implementation

POST /api/runs/{run_id}/pause through ControlApplicationService with stable 404/409/422-style error envelope.

### Acceptance

Pause route API tests pass.

---

## M8-CONTROL-020 — Resume REST Endpoint

### Dependencies

`M8-CONTROL-019`

### Owned Files

```text
backend/src/codex_flow/api/routes/controls.py
backend/tests/api/test_resume_route.py
```

### Implementation

POST /api/runs/{run_id}/resume; response reflects durable pause state and execution continuation request.

### Acceptance

Resume route tests pass.

---

## M8-CONTROL-021 — Retry REST Endpoint

### Dependencies

`M8-CONTROL-020`

### Owned Files

```text
backend/src/codex_flow/api/routes/controls.py
backend/tests/api/test_retry_route.py
```

### Implementation

POST /api/runs/{run_id}/tasks/{task_id}/retry; task_id accepts public task id or TaskRun id consistently with existing task routes.

### Acceptance

Retry route tests prove fresh attempt occurs only after scheduler start.

---

## M8-CONTROL-022 — Cancel REST Endpoint

### Dependencies

`M8-CONTROL-021`

### Owned Files

```text
backend/src/codex_flow/api/routes/controls.py
backend/tests/api/test_cancel_route.py
```

### Implementation

POST /api/runs/{run_id}/tasks/{task_id}/cancel with queued and running paths.

### Acceptance

Cancel API matrix passes.

---

## M8-CONTROL-023 — Skip REST Endpoint

### Dependencies

`M8-CONTROL-022`

### Owned Files

```text
backend/src/codex_flow/api/routes/controls.py
backend/tests/api/test_skip_route.py
```

### Implementation

POST /api/runs/{run_id}/tasks/{task_id}/skip and expose stable invalid-state error.

### Acceptance

Skip route tests pass.

---

## M8-CONTROL-024 — Mark-Success REST Endpoint

### Dependencies

`M8-CONTROL-023`

### Owned Files

```text
backend/src/codex_flow/api/routes/controls.py
backend/tests/api/test_mark_success_route.py
```

### Implementation

POST /api/runs/{run_id}/tasks/{task_id}/mark-success with explicit audit trail.

### Acceptance

Mark-success route and audit tests pass.

---

## M8-CONTROL-025 — Control API Error Matrix

### Dependencies

`M8-CONTROL-024`

### Owned Files

```text
backend/src/codex_flow/api/errors.py
backend/tests/api/test_control_error_matrix.py
```

### Implementation

Normalize unknown run/task, invalid state, paused/not-paused conflicts, runtime unavailable, and interrupt failure into stable error codes; never leak traceback/SDK details.

### Acceptance

Full control error matrix passes.

---

## M8-CONTROL-026 — Audit Events Through WebSocket

### Dependencies

`M8-CONTROL-025`

### Owned Files

```text
backend/src/codex_flow/application/events.py
backend/src/codex_flow/application/event_stream.py
backend/tests/integration/test_control_event_stream.py
```

### Implementation

Ensure manual action audit events carry workflow_run_id and flow through existing durable event stream/cursor without duplication.

### Acceptance

Pause/retry/cancel audit events appear in ordered stream and reconnect correctly.

---

## M8-CONTROL-027 — Paused Run Restart Recovery

### Dependencies

`M8-CONTROL-026`

### Owned Files

```text
backend/src/codex_flow/api/lifespan.py
backend/src/codex_flow/runtime/manager.py
backend/tests/integration/test_paused_restart.py
```

### Implementation

Restarting app with a paused unfinished run must reconcile active external work but must not release new tasks until explicit Resume.

### Acceptance

Paused restart preserves no-new-start guarantee.

---

## M8-CONTROL-028 — Retry Releases Blocked Descendants

### Dependencies

`M8-CONTROL-027`

### Owned Files

```text
backend/src/codex_flow/runtime/runner.py
backend/tests/integration/test_retry_dependency_release.py
```

### Implementation

After failed parent is retried and reaches SUCCESS, previously BLOCKED descendants become READY using canonical readiness logic.

### Acceptance

A fail -> B blocked -> Retry A success -> B executes exactly once.

---

## M8-CONTROL-029 — Retry Attempt Identity

### Dependencies

`M8-CONTROL-028`

### Owned Files

```text
backend/src/codex_flow/storage/attempts.py
backend/src/codex_flow/runtime/runner.py
backend/tests/integration/test_retry_attempt_identity.py
```

### Implementation

Verify each retry creates a distinct immutable Attempt and never reuses thread/turn refs from an older attempt.

### Acceptance

Attempt history shows stable distinct IDs and refs.

---

## M8-CONTROL-030 — Cancellation Race Matrix

### Dependencies

`M8-CONTROL-029`

### Owned Files

```text
backend/tests/integration/test_cancel_race_matrix.py
backend/src/codex_flow/runtime/runner.py
backend/src/codex_flow/runtime/manager.py
```

### Implementation

Cover cancel before thread, after thread before turn, RUNNING, and just before terminal persistence. No duplicate interrupt/prompt or terminal overwrite.

### Acceptance

All deterministic crash/race points pass.

---

## M8-UI-031 — Frontend Control Types

### Dependencies

`M8-UI-031A`

### Owned Files

```text
frontend/src/api/types.ts
frontend/src/api/types.test.ts
```

### Implementation

Mirror control response/error and paused run fields from public M8 API. Add SKIPPED to TaskStatus if missing.

### Acceptance

Frontend public types match OpenAPI contract and type tests pass; frontend `tsc -b` passes after the dedicated status-presentation remediation.

---

## M8-UI-031A — SKIPPED Status Presentation Repair

### Dependencies

`M8-CONTROL-030`

### Owned Files

```text
frontend/src/features/runs/status.ts
frontend/src/features/runs/status.test.ts
```

### Implementation

Repair the M8-UI-031 integration gap caused by adding the authoritative `SKIPPED` TaskStatus:

- add `SKIPPED` to `canonicalTaskStatuses`;
- add deterministic presentation mapping `SKIPPED -> { label: "Skipped", token: "skipped" }`;
- preserve UNKNOWN fail-visible behavior;
- do not modify any other status semantics;
- run the focused status tests and frontend `tsc -b`.

After this task passes, resume `M8-UI-031` exactly where it was blocked. Do not reimplement its already committed type changes.

### Acceptance

- status mapping tests include SKIPPED and pass;
- frontend `tsc -b` passes;
- no unrelated frontend status or styling changes.

---

## M8-UI-032A — Typed Control ApiClient Repair

### Dependencies

`M8-UI-031`

### Owned Files

```text
frontend/src/api/client.ts
frontend/src/api/client.test.ts
```

### Implementation

Add the six typed low-level control methods required by M8-UI-032 to the default ApiClient:

- `pauseRun(runId)`
- `resumeRun(runId)`
- `retryTask(runId, taskId)`
- `cancelTask(runId, taskId)`
- `skipTask(runId, taskId)`
- `markSuccessTask(runId, taskId)`

Requirements:

- use only the existing `requestJson` transport;
- return `ManualActionResponse`;
- use the authoritative M8 REST paths;
- URL-encode run/task ids;
- preserve stable ApiError propagation;
- do not add retries, state inference, or direct fetch usage outside the existing client boundary.

### Acceptance

- focused ApiClient tests cover all six endpoint mappings and encoded ids;
- stable API error propagation remains green;
- frontend `tsc -b` passes;
- no unrelated frontend files change.

---

## M8-UI-032 — Frontend Control API Client

### Dependencies

`M8-UI-032A`

### Owned Files

```text
frontend/src/features/runs/api.ts
frontend/src/features/runs/api.test.ts
```

### Implementation

Add pause/resume/retry/cancel/skip/markSuccess methods to RunApi using typed API client.

### Acceptance

Endpoint mapping and error propagation tests pass.

---

## M8-UI-033 — Run Controls Component Shell

### Dependencies

`M8-UI-032`

### Owned Files

```text
frontend/src/features/runs/RunControls.tsx
frontend/src/features/runs/RunControls.css
frontend/src/features/runs/RunControls.test.tsx
```

### Implementation

Create control area driven only by durable run/task state and explicit callbacks. Unsupported actions stay hidden/disabled.

### Acceptance

Visibility matrix by run/task state passes.

---

## M8-UI-034 — Pause & Resume UI

### Dependencies

`M8-UI-033`

### Owned Files

```text
frontend/src/features/runs/RunControls.tsx
frontend/src/features/runs/RunDetailPage.tsx
frontend/src/features/runs/RunControls.test.tsx
```

### Implementation

Wire pause/resume controls, pending state, API errors and post-action refresh/stream updates.

### Acceptance

Pause/resume UI tests pass.

---

## M8-UI-035 — Retry UI

### Dependencies

`M8-UI-034`

### Owned Files

```text
frontend/src/features/runs/TaskRunDrawer.tsx
frontend/src/features/runs/RunControls.tsx
frontend/src/features/runs/RunControls.test.tsx
```

### Implementation

Show Retry for FAILED/INTERRUPTED/NEEDS_ATTENTION only. Require explicit click; no automatic client retry.

### Acceptance

Retry visibility and invocation tests pass.

---

## M8-UI-036 — Cancel UI

### Dependencies

`M8-UI-035`

### Owned Files

```text
frontend/src/features/runs/TaskRunDrawer.tsx
frontend/src/features/runs/RunControls.tsx
frontend/src/features/runs/RunControls.test.tsx
```

### Implementation

Expose Cancel for allowed queued/active states and show progress while request is pending.

### Acceptance

Cancel state matrix passes.

---

## M8-UI-037 — Skip & Mark-Success UI

### Dependencies

`M8-UI-036`

### Owned Files

```text
frontend/src/features/runs/TaskRunDrawer.tsx
frontend/src/features/runs/RunControls.tsx
frontend/src/features/runs/RunControls.test.tsx
```

### Implementation

Expose Skip/Mark Success only for server-supported states; UI does not broaden state-machine semantics.

### Acceptance

Visibility/action tests pass.

---

## M8-UI-038 — Destructive Action Confirmation

### Dependencies

`M8-UI-037`

### Owned Files

```text
frontend/src/features/runs/ConfirmActionDialog.tsx
frontend/src/features/runs/ConfirmActionDialog.css
frontend/src/features/runs/RunControls.tsx
frontend/src/features/runs/ConfirmActionDialog.test.tsx
```

### Implementation

Require confirmation for Cancel, Skip and Mark Success. Retry/Pause/Resume remain one-step. Dialog is keyboard accessible.

### Acceptance

Confirm/cancel/focus tests pass.

---

## M8-UI-039 — Control Feedback & Conflict Recovery

### Dependencies

`M8-UI-038`

### Owned Files

```text
frontend/src/features/runs/RunControls.tsx
frontend/src/features/runs/RunDetailPage.tsx
frontend/src/features/runs/RunControls.test.tsx
```

### Implementation

Display stable action errors; on 409 refresh durable run/task state rather than guessing local state.

### Acceptance

409 refresh and normal success tests pass.

---

## M8-UI-040 — Attention Center

### Dependencies

`M8-UI-039`

### Owned Files

```text
frontend/src/features/attention/AttentionCenter.tsx
frontend/src/features/attention/AttentionCenter.css
frontend/src/features/attention/AttentionCenter.test.tsx
frontend/src/app/AppShell.tsx
```

### Implementation

Aggregate NEEDS_ATTENTION tasks from loaded run history/API, link to run/task, and show count. No background scheduling decisions.

### Acceptance

Attention count/list/navigation tests pass.

---

## M8-UI-041 — Browser Notification Adapter

### Dependencies

`M8-UI-040`

### Owned Files

```text
frontend/src/features/attention/notifications.ts
frontend/src/features/attention/notifications.test.ts
```

### Implementation

When browser Notification permission is already granted, notify once per newly observed NEEDS_ATTENTION task. Never auto-request permission; dedupe by TaskRun id.

### Acceptance

Granted/denied/default/dedupe tests pass.

---

## M8-INTEGRATE-042 — Human-in-the-loop Integration & Repair

### Dependencies

`M8-UI-041`

### Owned Files

```text
backend/src/codex_flow/**
backend/tests/**
frontend/src/**
```

### Implementation

Run end-to-end Fake flow: fail -> blocked child -> retry -> success -> child runs; pause/resume; queued cancel; running cancel; skip; mark-success; attention; audit WebSocket; UI controls. Bounded repairs allowed within M8 code only; do not alter frozen architecture.

### Acceptance

Integrated M8 flow passes; backend non-live + frontend test/typecheck/lint/build pass.

---

## M8-GATE-043 — M8 Reliability Acceptance Matrix

### Dependencies

`M8-INTEGRATE-042`

### Owned Files

```text
backend/src/codex_flow/**
backend/tests/**
frontend/src/**
```

### Implementation

Gate manual-control legality, audit completeness, race safety, pause persistence, retry attempt identity, downstream release/blocking, UI confirmations, attention center, notification adapter, M7/M6/M5 regressions. Do not weaken tests.

### Acceptance

Full M8 matrix plus existing non-live/backend/frontend regression passes.

---

## M8-REPORT-044 — M8 Milestone Report

### Dependencies

`M8-GATE-043`

### Owned Files

```text
docs/human-in-loop-reliability-test-report.md
```

### Implementation

Record PASS/FAIL evidence for every M8 control/reliability gate and list browser/native notification manual limits. On PASS advance to M9-DESKTOP-001.

### Acceptance

All required automated M8 gates are PASS with exact commands/counts.

---

# M9 — Desktop Integration & Packaging

## Goal

Package the completed local web product as a Windows Tauri desktop application with a Python backend sidecar, deterministic app-data storage, secure loopback communication, native attention/open-in-Codex bridges, and automated Windows build evidence.

## Frozen boundaries

- Tauri v2 + React frontend + Python/PyInstaller sidecar.
- Backend binds loopback only in desktop mode.
- A fresh per-process local token protects desktop REST/WebSocket endpoints.
- SQLite lives in user app-data, never the install directory.
- Codex authentication continues to use the real user HOME/USERPROFILE.
- No silent system toolchain installation; missing Rust/Windows build prerequisites are a genuine blocker.
- Automated packaging evidence is not a substitute for final manual visual UX checks.

## Deterministic Task Order

```text
M9-DESKTOP-001
↓
M9-DESKTOP-002
↓
M9-PREFLIGHT-003A
↓
M9-DESKTOP-003
↓
M9-DESKTOP-004
↓
M9-DESKTOP-005
↓
M9-DESKTOP-006
↓
M9-DESKTOP-007
↓
M9-DESKTOP-008
↓
M9-DESKTOP-009
↓
M9-DESKTOP-010
↓
M9-DESKTOP-011
↓
M9-DESKTOP-012
↓
M9-DESKTOP-013
↓
M9-DESKTOP-014
↓
M9-DESKTOP-015
↓
M9-DESKTOP-016
↓
M9-DESKTOP-017
↓
M9-DESKTOP-018
↓
M9-DESKTOP-019
↓
M9-DESKTOP-020
↓
M9-DESKTOP-021
↓
M9-DESKTOP-022
↓
M9-DESKTOP-023
↓
M9-DESKTOP-024
↓
M9-DESKTOP-025
↓
M9-DESKTOP-026
↓
M9-DESKTOP-027
↓
M9-DESKTOP-028
↓
M9-DESKTOP-029
↓
M9-DESKTOP-030
↓
M9-DESKTOP-031
↓
M9-DESKTOP-032
↓
M9-DESKTOP-033
↓
M9-DESKTOP-034
↓
M9-DESKTOP-035
↓
M9-DESKTOP-036
↓
M9-DESKTOP-037
↓
M9-DESKTOP-038
↓
M9-GATE-039
↓
M9-REPORT-040
```

Execute exactly in this order unless a genuine blocker occurs. Completion of an individual task is not a stop condition.

---

## M9-DESKTOP-001 — Desktop Architecture Contract

### Dependencies

`M8-REPORT-044`

### Owned Files

```text
docs/desktop-runtime-contract.md
desktop/README.md
```

### Implementation

Freeze Tauri v2 + React bundle + Python sidecar process contract, stdout handshake, loopback security, app-data DB/log paths, graceful shutdown, and no private Codex Desktop access.

### Acceptance

Contract is consistent with ADR-006/master roadmap and M8 API.

---

## M9-DESKTOP-002 — Tauri NPM Tooling

### Dependencies

`M9-DESKTOP-001`

### Owned Files

```text
frontend/package.json
frontend/package-lock.json
```

### Implementation

Add @tauri-apps/api and @tauri-apps/cli compatible v2 dependencies plus desktop dev/build scripts. Do not upgrade unrelated frontend deps.

### Acceptance

npm install, typecheck, lint, build remain green.

---

## M9-PREFLIGHT-003A — Windows Desktop Toolchain Preflight

### Dependencies

`M9-DESKTOP-002`

### Owned Files

```text
docs/m9-environment-preflight.md
```

### Implementation

Run one deterministic Windows desktop prerequisite audit before resuming Rust/Tauri implementation.

Check and record at minimum:

- Python 3.11+ and project virtual environment;
- Node and npm;
- PyInstaller availability from the project environment;
- `cargo`, `rustc`, and `rustup`;
- Microsoft C++/MSVC build tools presence using `vswhere`, `cl`, or installed Visual Studio Build Tools evidence;
- Windows SDK evidence required by the installed MSVC toolchain;
- WebView2 Runtime presence;
- Git;
- current relevant versions/paths.

Installation policy for this task:

- do not install any system component by default;
- if the user's current invocation explicitly authorizes the exact named `Rust toolchain`, and `cargo`/`rustc` are missing, install Rust only from the official Rustup source using a per-user, non-interactive supported mode, then refresh the current process PATH and verify `rustc --version` and `cargo --version`;
- that Rust authorization does not authorize Visual Studio Build Tools, Windows SDK, WebView2, or any other component;
- if another required component is missing, record all missing prerequisites together and BLOCK once with exact evidence and next action;
- do not request or perform a reboot, elevation, GUI installer flow, or license interaction.

If all required prerequisites are present after any explicitly authorized Rust installation, write the evidence report and clear the existing M9-DESKTOP-003 environment blocker.

### Acceptance

- `docs/m9-environment-preflight.md` records each declared prerequisite as PASS or BLOCKED with command/version evidence;
- if Rust installation was explicitly authorized and needed, official Rustup installation succeeds and `cargo --version` / `rustc --version` pass in the same invocation;
- all other required M9 toolchains are present without unapproved system installation;
- on PASS, resume M9-DESKTOP-003 automatically.

---

## M9-DESKTOP-003 — Tauri Rust Scaffold

### Dependencies

`M9-PREFLIGHT-003A`

### Owned Files

```text
desktop/src-tauri/Cargo.toml
desktop/src-tauri/build.rs
desktop/src-tauri/src/main.rs
desktop/src-tauri/tauri.conf.json
desktop/src-tauri/capabilities/default.json
```

### Implementation

Create minimal Tauri v2 Windows shell pointing at frontend dist/dev server. Keep permissions minimal.

### Acceptance

cargo metadata succeeds when Rust toolchain is available; config schema is valid.

---

## M9-DESKTOP-004 — Backend Server Entrypoint

### Dependencies

`M9-DESKTOP-003`

### Owned Files

```text
backend/src/codex_flow/server.py
backend/pyproject.toml
backend/tests/unit/test_server_cli.py
```

### Implementation

Add production uvicorn entrypoint independent of CLI workflow runner. Accept explicit host/port/db/token/log-dir args. Default host must be 127.0.0.1.

### Acceptance

Argument parsing and no-import-side-effect tests pass.

---

## M9-DESKTOP-005 — Loopback Binding Guard

### Dependencies

`M9-DESKTOP-004`

### Owned Files

```text
backend/src/codex_flow/server.py
backend/tests/unit/test_server_binding.py
```

### Implementation

Reject non-loopback bind addresses in desktop mode. Preserve local-service-only architecture.

### Acceptance

IPv4/IPv6 loopback accepted; wildcard/LAN binds rejected.

---

## M9-DESKTOP-006 — Local Session Token Middleware

### Dependencies

`M9-DESKTOP-005`

### Owned Files

```text
backend/src/codex_flow/api/app.py
backend/src/codex_flow/api/config.py
backend/tests/api/test_local_token.py
```

### Implementation

Support optional per-process bearer token for desktop mode. Health handshake may use dedicated token-safe path; all /api and /ws data endpoints require token when configured.

### Acceptance

Authorized/unauthorized REST tests pass; no token logged.

---

## M9-DESKTOP-007 — WebSocket Token Validation

### Dependencies

`M9-DESKTOP-006`

### Owned Files

```text
backend/src/codex_flow/api/routes/ws.py
backend/tests/api/test_ws_token.py
```

### Implementation

When desktop token configured, validate token via query parameter dedicated to local sidecar because browser WebSocket cannot set Authorization header reliably.

### Acceptance

Valid/invalid/missing token WS tests pass; query token never enters persisted events.

---

## M9-DESKTOP-008 — Sidecar Handshake Protocol

### Dependencies

`M9-DESKTOP-007`

### Owned Files

```text
backend/src/codex_flow/server.py
backend/tests/unit/test_server_handshake.py
```

### Implementation

After binding, print exactly one machine-readable readiness line containing version, loopback port and process id; token is not printed. Flush immediately.

### Acceptance

Handshake parser fixture and stdout ordering tests pass.

---

## M9-DESKTOP-009 — PyInstaller Sidecar Spec

### Dependencies

`M9-DESKTOP-008`

### Owned Files

```text
backend/codex_flow_sidecar.spec
backend/scripts/build_sidecar.py
```

### Implementation

Create reproducible Windows PyInstaller build for server entrypoint including openai-codex runtime requirements and migrations. Output to desktop sidecar staging directory.

### Acceptance

Spec analysis/build command generation tests pass; no secrets bundled.

---

## M9-DESKTOP-010 — Sidecar Build Smoke

### Dependencies

`M9-DESKTOP-009`

### Owned Files

```text
backend/tests/packaging/test_sidecar_build.py
backend/scripts/build_sidecar.py
```

### Implementation

Build sidecar executable when PyInstaller is available, launch --help/version smoke, and verify packaged migrations/resources are present.

### Acceptance

Packaging test passes or records precise missing toolchain only if external prerequisite truly absent.

---

## M9-DESKTOP-011 — Tauri External Binary Config

### Dependencies

`M9-DESKTOP-010`

### Owned Files

```text
desktop/src-tauri/tauri.conf.json
desktop/src-tauri/Cargo.toml
```

### Implementation

Declare Python backend executable as Tauri sidecar/externalBin with Windows target naming and no shell=True invocation.

### Acceptance

Tauri config validation passes.

---

## M9-DESKTOP-012 — Rust Sidecar Launcher

### Dependencies

`M9-DESKTOP-011`

### Owned Files

```text
desktop/src-tauri/src/sidecar.rs
desktop/src-tauri/src/main.rs
```

### Implementation

Launch backend sidecar with generated token, app-data DB/log paths and inherited Codex auth HOME. Capture stdout/stderr asynchronously.

### Acceptance

Rust unit/compile checks cover command construction.

---

## M9-DESKTOP-013 — Handshake Parsing in Tauri

### Dependencies

`M9-DESKTOP-012`

### Owned Files

```text
desktop/src-tauri/src/handshake.rs
desktop/src-tauri/src/sidecar.rs
desktop/src-tauri/src/handshake_test.rs
```

### Implementation

Parse only canonical readiness line, validate loopback port, enforce startup deadline, ignore non-handshake log lines.

### Acceptance

Parser malformed/timeout/valid tests pass.

---

## M9-DESKTOP-014 — Desktop Runtime State Command

### Dependencies

`M9-DESKTOP-013`

### Owned Files

```text
desktop/src-tauri/src/runtime_state.rs
desktop/src-tauri/src/main.rs
```

### Implementation

Expose Tauri command returning backend base URL and opaque session token to this webview only after readiness. No filesystem token persistence.

### Acceptance

Command returns unavailable before ready and exact state after ready.

---

## M9-DESKTOP-015 — Frontend Desktop Bridge

### Dependencies

`M9-DESKTOP-014`

### Owned Files

```text
frontend/src/desktop/runtime.ts
frontend/src/desktop/runtime.test.ts
```

### Implementation

Detect Tauri environment and invoke runtime-state command. Browser mode continues to use relative /api and /ws.

### Acceptance

Browser/Tauri detection tests pass.

---

## M9-DESKTOP-016 — Dynamic HTTP Base URL

### Dependencies

`M9-DESKTOP-015`

### Owned Files

```text
frontend/src/api/http.ts
frontend/src/api/client.ts
frontend/src/desktop/runtime.ts
frontend/src/api/client.test.ts
```

### Implementation

Allow injected runtime base URL and bearer token without changing browser defaults.

### Acceptance

Desktop URL/auth and browser-relative tests pass.

---

## M9-DESKTOP-017 — Dynamic WebSocket Base URL

### Dependencies

`M9-DESKTOP-016`

### Owned Files

```text
frontend/src/api/ws.ts
frontend/src/desktop/runtime.ts
frontend/src/api/ws.test.ts
```

### Implementation

Build ws://127.0.0.1:<port>/ws/... in desktop mode and append encoded token query; browser mode unchanged.

### Acceptance

Desktop/browser WS URL tests pass.

---

## M9-DESKTOP-018 — Strict Desktop CORS

### Dependencies

`M9-DESKTOP-017`

### Owned Files

```text
backend/src/codex_flow/api/app.py
backend/src/codex_flow/api/config.py
backend/tests/api/test_desktop_cors.py
```

### Implementation

When desktop mode enabled, allow only configured Tauri webview origins required by actual platform behavior; do not use '*' with credentials.

### Acceptance

Allowed/disallowed origin tests pass.

---

## M9-DESKTOP-019 — App Data Path Resolver

### Dependencies

`M9-DESKTOP-018`

### Owned Files

```text
desktop/src-tauri/src/paths.rs
desktop/src-tauri/src/main.rs
```

### Implementation

Resolve app-data directory via Tauri APIs, create Codex Flow subdirectories, normalize Windows paths, never store DB under install directory.

### Acceptance

Path tests cover spaces/non-ASCII and deterministic child names.

---

## M9-DESKTOP-020 — Desktop SQLite Location

### Dependencies

`M9-DESKTOP-019`

### Owned Files

```text
desktop/src-tauri/src/paths.rs
desktop/src-tauri/src/sidecar.rs
desktop/src-tauri/src/paths_test.rs
```

### Implementation

Pass app-data/codex-flow.sqlite3 to sidecar; reuse same path across launches.

### Acceptance

Path persistence tests pass.

---

## M9-DESKTOP-021 — Desktop Log Directory

### Dependencies

`M9-DESKTOP-020`

### Owned Files

```text
backend/src/codex_flow/server.py
desktop/src-tauri/src/paths.rs
desktop/src-tauri/src/sidecar.rs
backend/tests/unit/test_server_logging.py
```

### Implementation

Write rotating/plain bounded session logs under app-data logs without tokens; stdout handshake remains machine-readable.

### Acceptance

Log location/redaction tests pass.

---

## M9-DESKTOP-022 — Codex Authentication Environment Preservation

### Dependencies

`M9-DESKTOP-021`

### Owned Files

```text
desktop/src-tauri/src/sidecar.rs
desktop/src-tauri/src/sidecar_test.rs
```

### Implementation

Launch sidecar with canonical user HOME/USERPROFILE inherited; never redirect Codex auth to app-data. Preserve PATH needed for runtime.

### Acceptance

Environment-construction tests prove auth home is unchanged.

---

## M9-DESKTOP-023 — Backend Health Wait

### Dependencies

`M9-DESKTOP-022`

### Owned Files

```text
desktop/src-tauri/src/health.rs
desktop/src-tauri/src/sidecar.rs
```

### Implementation

After handshake, poll /healthz until ready with bounded timeout before marking runtime available.

### Acceptance

Ready/delayed/timeout tests pass.

---

## M9-DESKTOP-024 — Startup Failure Screen State

### Dependencies

`M9-DESKTOP-023`

### Owned Files

```text
frontend/src/desktop/DesktopStartupGate.tsx
frontend/src/desktop/DesktopStartupGate.css
frontend/src/desktop/DesktopStartupGate.test.tsx
frontend/src/App.tsx
```

### Implementation

In Tauri mode block normal routes until runtime ready; show actionable local error if sidecar fails, without exposing token/stack trace.

### Acceptance

Ready/loading/failure states test.

---

## M9-DESKTOP-025 — Graceful Sidecar Shutdown

### Dependencies

`M9-DESKTOP-024`

### Owned Files

```text
desktop/src-tauri/src/sidecar.rs
desktop/src-tauri/src/main.rs
```

### Implementation

On app exit request/perform deterministic sidecar termination after backend runtime shutdown opportunity; never leave duplicate child process.

### Acceptance

Rust lifecycle test/mocked child test passes.

---

## M9-DESKTOP-026 — Sidecar Crash Detection

### Dependencies

`M9-DESKTOP-025`

### Owned Files

```text
desktop/src-tauri/src/sidecar.rs
desktop/src-tauri/src/runtime_state.rs
frontend/src/desktop/DesktopStartupGate.tsx
```

### Implementation

Detect unexpected child exit, mark runtime unavailable and surface recovery UI. Do not silently start workflow actions against dead backend.

### Acceptance

Crash-state propagation tests pass.

---

## M9-DESKTOP-027 — Bounded Sidecar Relaunch

### Dependencies

`M9-DESKTOP-026`

### Owned Files

```text
desktop/src-tauri/src/sidecar.rs
desktop/src-tauri/src/runtime_state.rs
```

### Implementation

Allow one explicit user-triggered relaunch after crash using same DB path and fresh token. No automatic infinite restart loop.

### Acceptance

One-relaunch/no-loop tests pass.

---

## M9-DESKTOP-028 — Native Open-in-Codex Bridge

### Dependencies

`M9-DESKTOP-027`

### Owned Files

```text
desktop/src-tauri/src/open_external.rs
frontend/src/features/runs/OpenInCodex.tsx
frontend/src/features/runs/OpenInCodex.test.tsx
```

### Implementation

In Tauri mode open validated codex://threads/<id> using OS shell plugin/approved API; browser anchor remains fallback. Reject non-codex schemes.

### Acceptance

URI validation/bridge invocation tests pass.

---

## M9-DESKTOP-029 — Tauri Notification Capability

### Dependencies

`M9-DESKTOP-028`

### Owned Files

```text
desktop/src-tauri/Cargo.toml
desktop/src-tauri/capabilities/default.json
frontend/package.json
frontend/package-lock.json
```

### Implementation

Add Tauri notification plugin with minimum permission required for local attention notifications.

### Acceptance

Dependency/config validation passes.

---

## M9-DESKTOP-030 — Native Attention Notifications

### Dependencies

`M9-DESKTOP-029`

### Owned Files

```text
frontend/src/features/attention/notifications.ts
frontend/src/desktop/notifications.ts
frontend/src/desktop/notifications.test.ts
```

### Implementation

Use native Tauri notification in desktop mode for newly observed NEEDS_ATTENTION; browser adapter remains fallback. Dedupe unchanged.

### Acceptance

Desktop/browser notification adapter tests pass.

---

## M9-DESKTOP-031 — Single-instance Guard

### Dependencies

`M9-DESKTOP-030`

### Owned Files

```text
desktop/src-tauri/Cargo.toml
desktop/src-tauri/src/main.rs
desktop/src-tauri/src/single_instance.rs
```

### Implementation

Prevent a second Codex Flow desktop instance from launching another sidecar/DB writer; focus existing window instead.

### Acceptance

Single-instance callback tests/compile pass.

---

## M9-DESKTOP-032 — Window State Persistence

### Dependencies

`M9-DESKTOP-031`

### Owned Files

```text
desktop/src-tauri/src/window_state.rs
desktop/src-tauri/src/main.rs
```

### Implementation

Persist safe window size/position/maximized state only; clamp invalid off-screen coordinates. No workflow data in window state.

### Acceptance

State serialization/clamp tests pass.

---

## M9-DESKTOP-033 — Production Frontend Bundle Wiring

### Dependencies

`M9-DESKTOP-032`

### Owned Files

```text
frontend/vite.config.ts
desktop/src-tauri/tauri.conf.json
desktop/README.md
```

### Implementation

Configure Tauri devUrl/frontendDist correctly and ensure production bundle uses desktop runtime bridge rather than baked backend URL.

### Acceptance

npm build and Tauri config check pass.

---

## M9-DESKTOP-034 — One-command Desktop Dev Script

### Dependencies

`M9-DESKTOP-033`

### Owned Files

```text
scripts/dev_desktop.ps1
desktop/README.md
```

### Implementation

Create deterministic Windows developer script: verify prerequisites, build/start required pieces, launch tauri dev. Do not install system packages silently.

### Acceptance

PowerShell syntax/check mode passes and missing prerequisite messages are precise.

---

## M9-DESKTOP-035 — One-command Desktop Build Script

### Dependencies

`M9-DESKTOP-034`

### Owned Files

```text
scripts/build_desktop.ps1
desktop/README.md
```

### Implementation

Build frontend, Python sidecar, stage external binary, then tauri build in fixed order. Stop on first failure and print artifact paths.

### Acceptance

Script check/dry-run tests pass.

---

## M9-DESKTOP-036 — Packaged Sidecar Contract Test

### Dependencies

`M9-DESKTOP-035`

### Owned Files

```text
backend/tests/packaging/test_packaged_sidecar_contract.py
scripts/build_desktop.ps1
```

### Implementation

Against built sidecar: start temp DB/token, parse handshake, call health/system status, terminate cleanly. No live Codex turn.

### Acceptance

Packaged sidecar contract passes.

---

## M9-DESKTOP-037 — Desktop Integration Harness

### Dependencies

`M9-DESKTOP-036`

### Owned Files

```text
desktop/tests/desktop_integration.md
desktop/src-tauri/src/sidecar.rs
frontend/src/desktop/**
```

### Implementation

Automate what can be tested without human GUI: launch sidecar lifecycle, runtime state, auth token, app-data paths, crash/relaunch, frontend bridge. Bounded repairs within desktop/frontend desktop bridge.

### Acceptance

Automated desktop integration suite passes.

---

## M9-DESKTOP-038 — Windows Bundle Build

### Dependencies

`M9-DESKTOP-037`

### Owned Files

```text
desktop/src-tauri/tauri.conf.json
scripts/build_desktop.ps1
docs/windows-build-artifacts.md
```

### Implementation

Produce Windows Tauri bundle/installer artifact when toolchain is present. Record exact filenames, sizes and hashes; do not claim manual UX validation.

### Acceptance

Build succeeds and artifact manifest is generated.

---

## M9-GATE-039 — M9 Automated Desktop Gate

### Dependencies

`M9-DESKTOP-038`

### Owned Files

```text
backend/**
frontend/**
desktop/**
scripts/**
```

### Implementation

Run frontend, backend non-live, sidecar packaging, Rust/Tauri checks, Windows bundle build and security scans for token/log/path rules. Bounded M9 repairs allowed; no architecture redesign.

### Acceptance

All automated M9 gates pass; no private Codex Desktop state accessed.

---

## M9-REPORT-040 — M9 Desktop Packaging Report

### Dependencies

`M9-GATE-039`

### Owned Files

```text
docs/desktop-packaging-test-report.md
```

### Implementation

Record PASS/FAIL for sidecar build, Tauri bundle, startup/shutdown, app-data DB, auth home, token security, native notification bridge, Open-in-Codex bridge, regressions. Explicitly defer visual/manual Desktop checks.

### Acceptance

Automated M9 report complete and M10-HARDEN-001 becomes next.

---

# M10 — Real-world Beta / Hardening

## Goal

Close semantic parity gaps and harden the product against concurrency, continuation, transient failures, timeouts, crashes, high event volume, reconnects, long-running use, and packaged-sidecar restarts before handing off the final manual V1 checks.

## Frozen boundaries

- Unknown/ambiguous external execution always fails closed.
- Automatic retry is limited to explicitly transient failures and max_attempts.
- Independent work may run concurrently, same-workspace writes remain serialized.
- CONTINUE_THREAD remains explicit and serialized per thread.
- Stress tests must be deterministic; do not add random flaky timing.
- M10 automated PASS does not claim the final manual Desktop UX checks.

## Deterministic Task Order

```text
M10-HARDEN-001
↓
M10-HARDEN-002
↓
M10-HARDEN-003
↓
M10-HARDEN-004
↓
M10-HARDEN-005
↓
M10-HARDEN-006
↓
M10-HARDEN-007
↓
M10-HARDEN-008
↓
M10-HARDEN-009
↓
M10-HARDEN-010
↓
M10-HARDEN-011
↓
M10-HARDEN-012
↓
M10-HARDEN-013
↓
M10-HARDEN-014
↓
M10-HARDEN-015
↓
M10-HARDEN-016
↓
M10-HARDEN-017
↓
M10-HARDEN-018
↓
M10-HARDEN-019
↓
M10-HARDEN-020
↓
M10-HARDEN-021
↓
M10-HARDEN-022
↓
M10-HARDEN-023
↓
M10-HARDEN-024
↓
M10-HARDEN-025
↓
M10-HARDEN-026
↓
M10-HARDEN-027
↓
M10-HARDEN-028
↓
M10-HARDEN-029
↓
M10-HARDEN-030
↓
M10-HARDEN-031
↓
M10-HARDEN-032
↓
M10-HARDEN-033
↓
M10-HARDEN-034
↓
M10-GATE-035
↓
M10-REPORT-036
```

Execute exactly in this order unless a genuine blocker occurs. Completion of an individual task is not a stop condition.

---

## M10-HARDEN-001 — Runtime Parity Audit

### Dependencies

`M9-REPORT-040`

### Owned Files

```text
docs/runtime-parity-audit.md
backend/tests/integration/test_runtime_parity.py
```

### Implementation

Compare DurableRunner/RuntimeManager against frozen AsyncScheduler semantics: continuation, global concurrency, workspace lock, thread lock, retry, timeout, failure propagation. Turn gaps into explicit failing tests before fixes.

### Acceptance

Audit test identifies only known gaps; no speculative architecture changes.

---

## M10-HARDEN-002 — Durable CONTINUE_THREAD Execution

### Dependencies

`M10-HARDEN-001`

### Owned Files

```text
backend/src/codex_flow/runtime/runner.py
backend/tests/integration/test_durable_continuation.py
```

### Implementation

Implement CONTINUE_THREAD in durable runner using explicit successful source thread_id and new turn; never create a new thread for continuation.

### Acceptance

Durable continuation reuses source thread and creates distinct turn.

---

## M10-HARDEN-003 — Continuation Attempt Persistence

### Dependencies

`M10-HARDEN-002`

### Owned Files

```text
backend/src/codex_flow/storage/attempts.py
backend/src/codex_flow/runtime/runner.py
backend/tests/integration/test_continuation_attempt.py
```

### Implementation

Persist continuation Attempt before external resume/start-turn and record same source thread/new turn safely.

### Acceptance

Transaction-order and ref tests pass.

---

## M10-HARDEN-004 — Continuation Recovery Safety

### Dependencies

`M10-HARDEN-003`

### Owned Files

```text
backend/src/codex_flow/storage/recovery.py
backend/tests/integration/test_continuation_recovery.py
```

### Implementation

Crash/restart around continuation resume/turn start must never resend prompt when external execution is ambiguous.

### Acceptance

Continuation crash-point matrix passes fail-closed.

---

## M10-HARDEN-005 — Global Concurrency Setting

### Dependencies

`M10-HARDEN-004`

### Owned Files

```text
backend/src/codex_flow/api/config.py
backend/src/codex_flow/runtime/manager.py
backend/tests/unit/test_runtime_concurrency_config.py
```

### Implementation

Expose configurable positive global concurrency to runtime while keeping deterministic ordering.

### Acceptance

Validation/default tests pass.

---

## M10-HARDEN-006 — Parallel Ready Task Execution

### Dependencies

`M10-HARDEN-005`

### Owned Files

```text
backend/src/codex_flow/runtime/runner.py
backend/tests/integration/test_durable_parallel_ready.py
```

### Implementation

Execute independent READY tasks concurrently up to global limit rather than sequential loop; deterministic task selection order is preserved.

### Acceptance

Two independent delayed Fake tasks overlap; limit is respected.

---

## M10-HARDEN-007 — Durable Workspace Write Lock

### Dependencies

`M10-HARDEN-006`

### Owned Files

```text
backend/src/codex_flow/runtime/runner.py
backend/src/codex_flow/runtime/manager.py
backend/tests/integration/test_durable_workspace_lock.py
```

### Implementation

Reuse canonical WorkspaceLockManager so same-cwd write tasks serialize while different cwd tasks may overlap.

### Acceptance

Same/different workspace concurrency tests pass.

---

## M10-HARDEN-008 — Durable Thread Turn Lock

### Dependencies

`M10-HARDEN-007`

### Owned Files

```text
backend/src/codex_flow/runtime/runner.py
backend/tests/integration/test_durable_thread_lock.py
```

### Implementation

Reuse canonical ThreadTurnLockManager so continuation turns on same thread cannot overlap.

### Acceptance

Same-thread serialization tests pass.

---

## M10-HARDEN-009 — Persistent Fork/Join Runtime Test

### Dependencies

`M10-HARDEN-008`

### Owned Files

```text
backend/tests/integration/test_persistent_fork_join.py
```

### Implementation

Run A -> B/C -> D through DurableRunner with DB state, parallel B/C, exact join release and no premature D.

### Acceptance

Persistent fork/join passes under concurrency >1.

---

## M10-HARDEN-010 — Same-workspace Fork Serialization

### Dependencies

`M10-HARDEN-009`

### Owned Files

```text
backend/tests/integration/test_persistent_workspace_serialization.py
```

### Implementation

Fork B/C share cwd under workspace_write; prove they do not overlap while downstream D remains correct.

### Acceptance

Serialization timing/order test passes.

---

## M10-HARDEN-011 — Cross-run Global Capacity

### Dependencies

`M10-HARDEN-010`

### Owned Files

```text
backend/src/codex_flow/runtime/manager.py
backend/tests/integration/test_multi_run_capacity.py
```

### Implementation

Share one global limiter across simultaneous workflow runs in same process; per-workflow duplicate-run rule remains.

### Acceptance

Multiple workflows obey total concurrency ceiling.

---

## M10-HARDEN-012 — Transient Error Classification

### Dependencies

`M10-HARDEN-011`

### Owned Files

```text
backend/src/codex_flow/runtime/transient.py
backend/tests/unit/test_transient_classification.py
```

### Implementation

Classify only explicit SERVER_BUSY/transport-overload/disconnect signals as transient. Task failure, permission, invalid prompt, interrupt and unknown are non-transient.

### Acceptance

Classification table passes fail-closed.

---

## M10-HARDEN-013 — Deterministic Retry Backoff

### Dependencies

`M10-HARDEN-012`

### Owned Files

```text
backend/src/codex_flow/runtime/backoff.py
backend/tests/unit/test_backoff.py
```

### Implementation

Implement bounded deterministic exponential backoff with injectable sleeper; no jitter in core tests.

### Acceptance

Backoff sequence/cap tests pass.

---

## M10-HARDEN-014 — Automatic Server-busy Retry

### Dependencies

`M10-HARDEN-013`

### Owned Files

```text
backend/src/codex_flow/runtime/runner.py
backend/tests/integration/test_auto_retry_server_busy.py
```

### Implementation

Retry transient server-busy within TaskDefinition max_attempts; each attempt persisted separately and audited.

### Acceptance

Busy->success creates distinct Attempts and succeeds within limit.

---

## M10-HARDEN-015 — Automatic Transport Retry

### Dependencies

`M10-HARDEN-014`

### Owned Files

```text
backend/src/codex_flow/runtime/runner.py
backend/tests/integration/test_auto_retry_transport.py
```

### Implementation

Retry explicit transient transport failure only when safe before/after known attempt boundary; ambiguous external start remains fail-closed.

### Acceptance

Safe transport retry matrix passes without duplicate prompt.

---

## M10-HARDEN-016 — No Retry for Task Failure

### Dependencies

`M10-HARDEN-015`

### Owned Files

```text
backend/tests/integration/test_no_auto_retry_task_failure.py
```

### Implementation

Prove failed Codex task/tool, permission/validation failures, user interrupt and unknown errors never auto-retry.

### Acceptance

No-auto-retry matrix passes.

---

## M10-HARDEN-017 — Max Attempts Enforcement

### Dependencies

`M10-HARDEN-016`

### Owned Files

```text
backend/src/codex_flow/runtime/runner.py
backend/tests/integration/test_max_attempts.py
```

### Implementation

Enforce retry_policy.max_attempts across automatic and manual attempts consistently; manual retry beyond limit returns stable conflict.

### Acceptance

Attempt ceiling tests pass.

---

## M10-HARDEN-018 — Retry Audit Trail

### Dependencies

`M10-HARDEN-017`

### Owned Files

```text
backend/src/codex_flow/runtime/runner.py
backend/tests/integration/test_auto_retry_audit.py
```

### Implementation

Record AUTO_RETRY_SCHEDULED/EXHAUSTED with attempt numbers and reason class, excluding secrets.

### Acceptance

Audit order/payload tests pass.

---

## M10-HARDEN-019 — Task Timeout Enforcement

### Dependencies

`M10-HARDEN-018`

### Owned Files

```text
backend/src/codex_flow/runtime/runner.py
backend/tests/integration/test_task_timeout.py
```

### Implementation

Honor timeout_seconds around turn execution. On timeout request interrupt, persist non-success terminal state/audit, and never release children.

### Acceptance

Timeout blocks child and calls interrupt at most once.

---

## M10-HARDEN-020 — Timeout vs Terminal Race

### Dependencies

`M10-HARDEN-019`

### Owned Files

```text
backend/tests/integration/test_timeout_terminal_race.py
backend/src/codex_flow/runtime/runner.py
```

### Implementation

Cover terminal arriving just before/after timeout; persist exactly one canonical outcome without overwrite.

### Acceptance

Race matrix passes deterministically.

---

## M10-HARDEN-021 — Timeout Restart Recovery

### Dependencies

`M10-HARDEN-020`

### Owned Files

```text
backend/tests/integration/test_timeout_restart.py
backend/src/codex_flow/storage/recovery.py
```

### Implementation

Kill process during timeout/interrupt boundary; restart must not resend prompt or release downstream from ambiguity.

### Acceptance

Restart timeout crash points pass.

---

## M10-HARDEN-022 — SQLite Busy Timeout & WAL Guard

### Dependencies

`M10-HARDEN-021`

### Owned Files

```text
backend/src/codex_flow/storage/db.py
backend/tests/integration/test_sqlite_busy.py
```

### Implementation

Configure bounded busy_timeout and verify WAL/foreign-key settings for concurrent API/runtime reads/writes. Do not hide persistent lock errors.

### Acceptance

Concurrent transaction tests pass.

---

## M10-HARDEN-023 — Storage Query Index Migration

### Dependencies

`M10-HARDEN-022`

### Owned Files

```text
backend/src/codex_flow/storage/migrations/0003_query_indexes.sql
backend/src/codex_flow/storage/schema.py
backend/tests/integration/test_migration_0003.py
```

### Implementation

Add indexes for workflow_runs workflow/status, task_runs run/status, attempts task, events run/created_at/id after measuring query patterns. No semantic schema changes.

### Acceptance

Fresh/v1/v2 upgrade and query-plan assertions pass.

---

## M10-HARDEN-024 — Large DAG Determinism

### Dependencies

`M10-HARDEN-023`

### Owned Files

```text
backend/tests/stress/test_large_dag.py
```

### Implementation

Generate deterministic 100-node mixed chain/fork/join DAG with Fake adapter; verify topology, readiness, completion, no duplicates.

### Acceptance

Repeated runs produce identical terminal/status ordering under deterministic fake timings.

---

## M10-HARDEN-025 — High Event Volume

### Dependencies

`M10-HARDEN-024`

### Owned Files

```text
backend/tests/stress/test_event_volume.py
backend/src/codex_flow/application/event_stream.py
```

### Implementation

Exercise thousands of persisted events and cursor reads; prove no duplication/loss and bounded polling behavior.

### Acceptance

Event-volume correctness test passes within documented local threshold.

---

## M10-HARDEN-026 — WebSocket Reconnect Storm

### Dependencies

`M10-HARDEN-025`

### Owned Files

```text
backend/tests/api/test_ws_reconnect_stress.py
frontend/src/features/runs/useRunStream.test.ts
```

### Implementation

Simulate repeated disconnect/reconnect clients with cursor resume while run progresses. Execution must be unaffected and events deduplicated.

### Acceptance

Reconnect stress passes without duplicate UI events.

---

## M10-HARDEN-027 — Concurrent API Read/Control Stress

### Dependencies

`M10-HARDEN-026`

### Owned Files

```text
backend/tests/stress/test_api_control_concurrency.py
```

### Implementation

Issue concurrent run/task reads with pause/resume/retry/cancel attempts using Fake runtime; invalid races return stable conflicts, DB remains consistent.

### Acceptance

Stress test ends with valid states and audit trail.

---

## M10-HARDEN-028 — Crash Fault Matrix Expansion

### Dependencies

`M10-HARDEN-027`

### Owned Files

```text
backend/tests/stress/test_crash_fault_matrix.py
```

### Implementation

Expand deterministic crash points across attempt commit, thread creation, turn start, RUNNING, manual control, retry, continuation and terminal persistence.

### Acceptance

Every ambiguous external state fails closed; no duplicate prompt evidence.

---

## M10-HARDEN-029 — Duplicate Prevention Property Matrix

### Dependencies

`M10-HARDEN-028`

### Owned Files

```text
backend/tests/stress/test_duplicate_prevention_matrix.py
```

### Implementation

Generate many deterministic event/crash/control sequences and assert at most one external prompt per Attempt plus no downstream release without SUCCESS.

### Acceptance

Property-style deterministic matrix passes without random seed dependence.

---

## M10-HARDEN-030 — Frontend Degraded Backend Recovery

### Dependencies

`M10-HARDEN-029`

### Owned Files

```text
frontend/src/api/client.test.ts
frontend/src/features/runs/RunDetailPage.test.tsx
frontend/src/desktop/DesktopStartupGate.test.tsx
```

### Implementation

Cover temporary 503, malformed response, WS loss and backend restart. UI must show error/reconnect without inventing task state.

### Acceptance

Degraded-mode frontend matrix passes.

---

## M10-HARDEN-031 — Desktop Sidecar Restart Soak

### Dependencies

`M10-HARDEN-030`

### Owned Files

```text
desktop/src-tauri/src/sidecar.rs
desktop/tests/sidecar_restart_matrix.md
```

### Implementation

Automate repeated sidecar start/crash/relaunch cycles against same temp app-data DB, validating no duplicate run/attempt/prompt in Fake mode.

### Acceptance

Bounded restart loop passes and cleans all child processes.

---

## M10-HARDEN-032 — Accelerated Long-run Soak

### Dependencies

`M10-HARDEN-031`

### Owned Files

```text
backend/tests/stress/test_soak.py
frontend/src/features/runs/useRunStream.test.ts
```

### Implementation

Run many accelerated Fake workflows/events/reconnects over repeated iterations without wall-clock sleeping. Check task leaks, pending asyncio tasks, DB consistency and memory-growth proxy counts.

### Acceptance

Soak loop completes cleanly with no leaked runtime tasks.

---

## M10-HARDEN-033 — Full Product Regression

### Dependencies

`M10-HARDEN-032`

### Owned Files

```text
frontend/**
backend/**
desktop/**
scripts/**
```

### Implementation

Run all non-live backend tests, frontend tests/typecheck/lint/build, packaging contract, Rust/Tauri checks and stress suite. Bounded repairs allowed within frozen M0-M10 architecture; no test weakening.

### Acceptance

Complete automated regression passes.

---

## M10-HARDEN-034 — V1 Acceptance Evidence Matrix

### Dependencies

`M10-HARDEN-033`

### Owned Files

```text
docs/v1-acceptance-evidence.md
backend/tests/**
frontend/src/**
desktop/**
```

### Implementation

Map every docs/v1-acceptance.md item to automated/manual evidence. Add missing automated checks where possible. Manual-only items must be explicitly marked pending, not guessed PASS.

### Acceptance

Evidence matrix is complete with no unsupported claims.

---

## M10-GATE-035 — M10 Automated Beta Gate

### Dependencies

`M10-HARDEN-034`

### Owned Files

```text
backend/**
frontend/**
desktop/**
scripts/**
docs/v1-acceptance-evidence.md
```

### Implementation

Final automated beta gate: concurrency, locks, continuation, retries, timeouts, controls, recovery, crash matrix, large DAG, event volume, frontend degradation, desktop sidecar/package regression. Do not run live Codex unless task explicitly says so.

### Acceptance

All automated hardening gates pass; known manual checks remain isolated.

---

## M10-REPORT-036 — M10 Hardening Report & Manual Gate Handoff

### Dependencies

`M10-GATE-035`

### Owned Files

```text
docs/beta-hardening-test-report.md
docs/manual-v1-checklist.md
```

### Implementation

Record exact automated results and create final concise manual checklist for installer launch, native notification appearance, Open-in-Codex actual Desktop behavior, sidebar/search visibility and no-manual-Enter observation. Set next_task null after PASS.

### Acceptance

M10 automated report PASS; manual checklist exists; project waits for user manual V1 verification.

---

