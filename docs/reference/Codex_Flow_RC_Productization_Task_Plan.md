# Codex Flow — Release Candidate & Productization Plan (M11–M12)

This plan extends the automated execution pool after M10. It is intentionally composed of medium-granularity work that improves real release quality rather than subdividing trivial edits.

Estimated additional autonomous work at the project's observed velocity: roughly 4.5–7 hours. Together with the remaining M10 hardening, the intended pool is roughly 7–10 hours, subject to actual defects/build time.

Global constraints:

- Follow AGENTS.md and .codex/AUTO_EXECUTION.md.
- M11/M12 are local/offline by default: no live Codex execution, external web research, package downloads, or new system toolchains unless a later explicit user instruction authorizes them.
- No new third-party Python/Node/Rust runtime dependency is required by this plan. Prefer Python/JS/Rust standard facilities and already-installed project dependencies.
- SQLite remains authoritative durable state.
- The deterministic scheduler architecture remains frozen.
- No cloud/multi-user/account system.
- No private Codex Desktop database/IPC/state access.
- All subjective/manual GUI checks remain deferred to the final handoff so autonomous execution is not interrupted.
- Bounded adjacent integration repairs should be auto-remediated under the repository protocol.

# M11 — Release Candidate / Real-world Validation

## Goal

Exercise the completed local desktop product under realistic Windows paths, persistence/restart conditions, larger workflows, repeated runs, sidecar lifecycle and release-build conditions so the codebase reaches an evidence-backed release-candidate state.

## Frozen boundaries

- No new external/system dependency or download.
- No live Codex turn is required; use FakeCodexAdapter for deterministic execution tests.
- Do not install/uninstall MSI/NSIS automatically or require manual GUI interaction.
- Path/restart/build tests must use temporary/user-safe locations and clean only their own fixtures.
- Release artifact verification may read existing artifacts; rebuilding uses only already-present caches/toolchains.

## Deterministic Task Order

```text
M11-RC-001
↓
M11-FIXTURE-002
↓
M11-PATH-003
↓
M11-PATH-004
↓
M11-PATH-005
↓
M11-PATH-006
↓
M11-DATA-007
↓
M11-DATA-008
↓
M11-DATA-009
↓
M11-DATA-010
↓
M11-RECOVERY-011
↓
M11-RECOVERY-012
↓
M11-RECOVERY-013
↓
M11-RECOVERY-014
↓
M11-RECOVERY-015
↓
M11-WORKFLOW-016
↓
M11-WORKFLOW-017
↓
M11-WORKFLOW-018
↓
M11-WORKFLOW-019
↓
M11-WORKFLOW-020
↓
M11-WORKFLOW-021
↓
M11-WORKFLOW-022
↓
M11-API-023
↓
M11-WS-024
↓
M11-DESKTOP-025
↓
M11-DESKTOP-026
↓
M11-DESKTOP-027
↓
M11-DESKTOP-028
↓
M11-DESKTOP-029
↓
M11-LOG-030
↓
M11-LOG-031
↓
M11-BUILD-032
↓
M11-BUILD-033
↓
M11-BUILD-034
↓
M11-GATE-035
↓
M11-REPORT-036
```

Execute exactly in order unless a genuine blocker occurs. Bounded remediation follows AGENTS.md and .codex/AUTO_EXECUTION.md and is not a reason to stop.

---

## M11-RC-001 — Release Candidate Contract & Preflight

### Dependencies

`M10-REPORT-036`

### Owned Files

```text
docs/rc-validation-contract.md
backend/tests/rc/test_rc_preflight.py
```

### Implementation

Freeze M11 as offline/local release-candidate validation. Audit that the already-approved toolchain needed by M11 is present: project Python/venv, Node/npm, Rust/Cargo, PyInstaller, Git, and existing Tauri build inputs. Do not install or download anything. Explicitly prohibit live Codex/network/manual GUI requirements inside M11.

### Acceptance

RC contract records PASS/BLOCKED for declared prerequisites; the preflight test uses only existing local tools and introduces no new dependency.

---

## M11-FIXTURE-002 — RC Fixture Factory

### Dependencies

`M11-RC-001`

### Owned Files

```text
backend/tests/rc/fixtures.py
backend/tests/rc/test_fixtures.py
```

### Implementation

Create reusable deterministic helpers for temporary app-data directories, workflow definitions, FakeCodexAdapter scenarios, persisted SQLite runs, and process lifecycle probes. Fixtures must avoid wall-clock sleeps where injectable synchronization can be used.

### Acceptance

Fixture tests pass and later M11 tests can reuse them without global mutable state.

---

## M11-PATH-003 — Workspace Path With Spaces

### Dependencies

`M11-FIXTURE-002`

### Owned Files

```text
backend/tests/rc/test_workspace_paths.py
```

### Implementation

Execute a durable Fake workflow whose cwd contains multiple spaces and nested directories. Verify canonical workspace locking, persistence, and no path truncation.

### Acceptance

Space-containing workspace completes and persists exact cwd; no duplicate execution.

---

## M11-PATH-004 — Unicode Workspace Path

### Dependencies

`M11-PATH-003`

### Owned Files

```text
backend/tests/rc/test_workspace_paths.py
```

### Implementation

Exercise a durable workflow under a Windows-safe Unicode/non-ASCII path. Verify SQLite snapshot, path locking, event persistence, and cleanup preserve the exact path.

### Acceptance

Unicode workspace test passes without lossy normalization or encoding failures.

---

## M11-PATH-005 — Deep Nested Workspace Path

### Dependencies

`M11-PATH-004`

### Owned Files

```text
backend/tests/rc/test_workspace_paths.py
```

### Implementation

Exercise a reasonably deep nested path below normal Windows limits, including spaces and Unicode segments, to catch quoting/path-join regressions.

### Acceptance

Deep-path workflow completes and all generated fixture files remain under the intended root.

---

## M11-PATH-006 — Missing Workspace Fail-visible Behavior

### Dependencies

`M11-PATH-005`

### Owned Files

```text
backend/tests/rc/test_missing_workspace.py
```

### Implementation

Start a workflow whose configured cwd is removed before execution. Require deterministic fail-visible behavior; it must not silently fall back to repository root or another cwd.

### Acceptance

Missing cwd cannot execute in an unintended directory; result is deterministic and downstream work is not released.

---

## M11-DATA-007 — Database Reopen Persistence

### Dependencies

`M11-PATH-006`

### Owned Files

```text
backend/tests/rc/test_database_reopen.py
```

### Implementation

Create workflows/runs/tasks/attempts/events, close the connection cleanly, reopen the same DB, and verify identifiers, snapshots, statuses, control metadata, and event ordering are preserved.

### Acceptance

Reopen matrix passes with exact durable state.

---

## M11-DATA-008 — Full Migration Chain Rehearsal

### Dependencies

`M11-DATA-007`

### Owned Files

```text
backend/tests/rc/test_full_migration_chain.py
backend/src/codex_flow/storage/schema.py
```

### Implementation

Exercise supported historical schema fixtures through the latest migration in one test matrix, then reopen again to prove idempotence. Bounded remediation may repair migration discovery only; no semantic data rewrite.

### Acceptance

Fresh and historical DB fixtures migrate to latest schema and reopen idempotently.

---

## M11-DATA-009 — Event Cursor Across Restart

### Dependencies

`M11-DATA-008`

### Owned Files

```text
backend/tests/rc/test_event_cursor_restart.py
```

### Implementation

Persist events, consume to a cursor, recreate application/event-stream objects against the same DB, then resume after the cursor with no loss or duplication.

### Acceptance

Restarted cursor delivery returns only later events in stable order.

---

## M11-DATA-010 — Attempt History Across Restart

### Dependencies

`M11-DATA-009`

### Owned Files

```text
backend/tests/rc/test_attempt_history_restart.py
```

### Implementation

Create retry history with multiple immutable Attempts, restart storage/runtime objects, and verify all attempt IDs/status/thread/turn references remain queryable and ordered.

### Acceptance

Attempt history survives restart exactly and no attempt is overwritten.

---

## M11-RECOVERY-011 — Queued Run Restart

### Dependencies

`M11-DATA-010`

### Owned Files

```text
backend/tests/rc/test_restart_matrix.py
```

### Implementation

Restart after run creation before the first external turn begins. Require a deterministic safe outcome with no duplicate prompt and no accidental downstream release.

### Acceptance

Queued/start boundary restart matrix passes fail-closed.

---

## M11-RECOVERY-012 — Paused Run Restart RC

### Dependencies

`M11-RECOVERY-011`

### Owned Files

```text
backend/tests/rc/test_restart_matrix.py
```

### Implementation

Revalidate a paused run over full application recreation: active work may reconcile, but no new task starts until explicit Resume.

### Acceptance

Paused run remains paused across recreation and resumes exactly once.

---

## M11-RECOVERY-013 — Needs-Attention Restart RC

### Dependencies

`M11-RECOVERY-012`

### Owned Files

```text
backend/tests/rc/test_restart_matrix.py
```

### Implementation

Persist NEEDS_ATTENTION, recreate application/runtime, and verify it remains user-visible/actionable without silently converting to success or rerunning prompt.

### Acceptance

NEEDS_ATTENTION restart is durable and no duplicate prompt is observed.

---

## M11-RECOVERY-014 — Manual Control + Restart Matrix

### Dependencies

`M11-RECOVERY-013`

### Owned Files

```text
backend/tests/rc/test_control_restart_matrix.py
```

### Implementation

Cover pause, resume, queued cancel, running cancel, skip, mark-success, and retry around application recreation. Validate audit events and downstream readiness after restart.

### Acceptance

Control/restart matrix ends only in canonical states with complete audit evidence.

---

## M11-RECOVERY-015 — Multiple Runs Restart Matrix

### Dependencies

`M11-RECOVERY-014`

### Owned Files

```text
backend/tests/rc/test_multi_run_restart.py
```

### Implementation

Persist several workflows in mixed states, recreate application/runtime, and verify each run restores independently with no cross-workflow thread/task mix-up.

### Acceptance

Multi-run restart preserves workflow/run isolation and unique execution identity.

---

## M11-WORKFLOW-016 — 20-node Mixed DAG Scenario

### Dependencies

`M11-RECOVERY-015`

### Owned Files

```text
backend/tests/rc/test_complex_workflows.py
```

### Implementation

Build a deterministic 20-node workflow mixing chains, forks, joins, independent workspaces and explicit continuations where valid. Run with Fake adapter and verify every node starts exactly when dependencies allow.

### Acceptance

All 20 tasks reach expected terminal states with no duplicate prompt or premature join.

---

## M11-WORKFLOW-017 — Mixed Failure/Recovery Scenario

### Dependencies

`M11-WORKFLOW-016`

### Owned Files

```text
backend/tests/rc/test_complex_workflows.py
```

### Implementation

Exercise a medium DAG with one failure, blocked descendants, retry, pause/resume, skip on a separate branch, and eventual deterministic completion/failure semantics.

### Acceptance

Failure/recovery scenario preserves canonical blocking and attempt history.

---

## M11-WORKFLOW-018 — Continuation Chain Scenario

### Dependencies

`M11-WORKFLOW-017`

### Owned Files

```text
backend/tests/rc/test_complex_workflows.py
```

### Implementation

Exercise several valid CONTINUE_THREAD steps interleaved with NEW_THREAD branches and a join. Verify thread reuse only where explicitly configured.

### Acceptance

Continuation source threads are exact; unrelated branches never inherit a thread.

---

## M11-WORKFLOW-019 — Parallel Independent Workspaces

### Dependencies

`M11-WORKFLOW-018`

### Owned Files

```text
backend/tests/rc/test_parallel_workflows.py
```

### Implementation

Run multiple READY tasks in distinct workspace_write directories under configured concurrency and prove overlap using synchronization markers rather than flaky sleep thresholds.

### Acceptance

Independent work overlaps within capacity and final DAG state is deterministic.

---

## M11-WORKFLOW-020 — Same-workspace Serialization RC

### Dependencies

`M11-WORKFLOW-019`

### Owned Files

```text
backend/tests/rc/test_parallel_workflows.py
```

### Implementation

Run sibling write tasks sharing one canonical cwd, including equivalent path spellings, and prove the workspace lock serializes them.

### Acceptance

Equivalent same-workspace paths never overlap.

---

## M11-WORKFLOW-021 — Repeated Run Isolation

### Dependencies

`M11-WORKFLOW-020`

### Owned Files

```text
backend/tests/rc/test_repeated_runs.py
```

### Implementation

Run the same workflow definition repeatedly against one database. Verify each WorkflowRun and TaskRun/Attempt set is isolated and no previous thread/turn refs bleed into later runs.

### Acceptance

Repeated runs have distinct durable identities and independent events.

---

## M11-WORKFLOW-022 — 50-run History Durability

### Dependencies

`M11-WORKFLOW-021`

### Owned Files

```text
backend/tests/rc/test_repeated_runs.py
```

### Implementation

Create and complete 50 deterministic Fake runs across multiple workflows and reopen the DB. Validate list ordering, task/attempt lookup, and no missing run rows.

### Acceptance

50-run history persists and query results remain complete and deterministic.

---

## M11-API-023 — Release Candidate API Lifecycle Smoke

### Dependencies

`M11-WORKFLOW-022`

### Owned Files

```text
backend/tests/rc/test_api_rc_smoke.py
```

### Implementation

Using the in-process FastAPI app with Fake adapter, create/save workflow, start run, stream/poll status, exercise one manual control path, and query attempts/events after completion.

### Acceptance

End-to-end local API lifecycle passes without live Codex or network access.

---

## M11-WS-024 — WebSocket Resume After App Recreation

### Dependencies

`M11-API-023`

### Owned Files

```text
backend/tests/rc/test_ws_restart.py
```

### Implementation

Simulate a client cursor, recreate the FastAPI app over the same DB, reconnect with after=<cursor>, and verify durable snapshot/event semantics.

### Acceptance

Reconnected client receives correct snapshot and only non-duplicate post-cursor events.

---

## M11-DESKTOP-025 — Rapid Sidecar Start/Stop Cycles

### Dependencies

`M11-WS-024`

### Owned Files

```text
desktop/src-tauri/src/sidecar.rs
desktop/tests/sidecar_rc_matrix.md
```

### Implementation

Automate repeated start -> ready -> graceful shutdown cycles against temporary app-data, verifying child cleanup and stable handshake parsing. Use existing packaged/local sidecar only; no downloads.

### Acceptance

Bounded repeated cycles leave no child processes owned by the harness and no DB corruption.

---

## M11-DESKTOP-026 — Sidecar Crash/Relaunch Persistence

### Dependencies

`M11-DESKTOP-025`

### Owned Files

```text
desktop/src-tauri/src/sidecar.rs
desktop/tests/sidecar_rc_matrix.md
```

### Implementation

Crash the sidecar after durable state exists, perform the already-supported bounded relaunch, and verify same DB path/fresh token/recovery state without duplicate execution.

### Acceptance

Crash/relaunch matrix passes with durable state preserved.

---

## M11-DESKTOP-027 — Single-instance Burst

### Dependencies

`M11-DESKTOP-026`

### Owned Files

```text
desktop/src-tauri/src/single_instance.rs
desktop/tests/single_instance_rc.md
```

### Implementation

Exercise a burst of secondary-instance callbacks against the existing single-instance logic and verify only the primary owns a sidecar while focus requests remain harmless/idempotent.

### Acceptance

Burst test passes without multiple sidecars or state mutation.

---

## M11-DESKTOP-028 — Session Token Renewal Across Relaunch

### Dependencies

`M11-DESKTOP-027`

### Owned Files

```text
backend/tests/rc/test_desktop_token_relaunch.py
desktop/src-tauri/src/runtime_state.rs
```

### Implementation

Verify a relaunched sidecar gets a fresh token, old token is rejected, new token authorizes REST/WS, and no token is persisted to logs/events/files.

### Acceptance

Token renewal matrix passes with old-token rejection and redaction.

---

## M11-DESKTOP-029 — App-data Path Real Harness

### Dependencies

`M11-DESKTOP-028`

### Owned Files

```text
desktop/src-tauri/src/paths.rs
desktop/tests/app_data_rc.md
```

### Implementation

Run path resolution/lifecycle harness with spaces and Unicode in the simulated/temporary user-data root. Verify DB/log/window-state paths remain under the selected app-data root.

### Acceptance

All desktop writable state resolves below app-data and handles Unicode/spaces.

---

## M11-LOG-030 — Crash Log Secret Redaction

### Dependencies

`M11-DESKTOP-029`

### Owned Files

```text
backend/tests/rc/test_log_redaction_rc.py
backend/src/codex_flow/server.py
```

### Implementation

Emit representative startup, API, token rejection, exception, and shutdown log records and verify bearer/query tokens, prompts, and obvious credential-like values are not exposed.

### Acceptance

Secret-redaction matrix passes; diagnostics remain useful without sensitive payloads.

---

## M11-LOG-031 — Bounded Log Retention

### Dependencies

`M11-LOG-030`

### Owned Files

```text
backend/src/codex_flow/server.py
backend/tests/rc/test_log_retention.py
```

### Implementation

Ensure desktop session logs have a deterministic bounded retention policy using standard library facilities only. Preserve current log location and avoid deleting non-Codex-Flow files.

### Acceptance

Retention test proves bounded log files and safe directory scoping.

---

## M11-BUILD-032 — Artifact Manifest Verifier

### Dependencies

`M11-LOG-031`

### Owned Files

```text
scripts/verify_release_artifacts.ps1
docs/windows-build-artifacts.md
```

### Implementation

Add a read-only verifier for the recorded release executable/MSI/NSIS artifact paths, sizes and SHA256 hashes. It must not rebuild or download anything.

### Acceptance

Verifier succeeds for current artifacts and fails visibly on tampered hash/size fixtures.

---

## M11-BUILD-033-R1 — Installer-independent Build Idempotency Path

### Dependencies

`M11-BUILD-032`

### Owned Files

```text
scripts/build_desktop.ps1
desktop/tests/build_idempotency.md
```

### Implementation

Add an explicit bundle-target selector to the existing desktop build script without changing its default release behavior.

Requirements:

- default invocation remains the existing full Windows bundle pipeline (`all`);
- support an explicit `nsis` mode that passes the authoritative Tauri CLI bundle selector instead of building MSI;
- optionally support explicit `msi` for symmetry, but do not add new tools or configuration;
- frontend build, PyInstaller sidecar staging, Tauri executable build, artifact paths, fail-fast behavior, and cleanup/order semantics remain unchanged;
- do not suppress WiX validation, modify Windows Installer service state, enable Windows optional features, or weaken MSI configuration;
- no network, package download, system installation, elevation, or reboot;
- dry-run output must show the selected bundle target clearly.

This remediation exists because the host Windows Installer service is unavailable during WiX ICE validation. M9 already contains successful MSI and NSIS build evidence. M11 idempotency must test repository-controlled staging/build repeatability without making the external MSI service a prerequisite.

### Acceptance

- default dry-run preserves full-bundle behavior;
- explicit NSIS dry-run emits a Tauri build using the NSIS bundle target;
- invalid bundle-target values fail visibly;
- no MSI/WiX or system-service behavior is changed;
- focused PowerShell parser/dry-run checks pass.

---

## M11-BUILD-033 — Repeated Build Idempotency

### Dependencies

`M11-BUILD-033-R1`

### Owned Files

```text
scripts/build_desktop.ps1
desktop/tests/build_idempotency.md
```

### Implementation

Run the desktop build pipeline twice from the same repository state and verify staging cleanup/order does not accumulate stale sidecars or change authoritative artifact discovery.

Use the default full bundle mode when the host MSI/WiX environment is available.

If the already-observed Windows Installer service failure persists, use the explicit NSIS bundle mode introduced by M11-BUILD-033-R1 for both idempotency runs. This is not an MSI PASS claim: preserve the existing M9 MSI evidence separately and record that MSI was not rebuilt in M11 because of the external host service.

Do not require byte-identical installer outputs. Do not modify Windows services, optional Windows features, firewall/security settings, or system installers.

### Acceptance

- two consecutive builds from the same repository state succeed using one consistent approved bundle mode;
- frontend/sidecar/Tauri staging remains clean between runs;
- current release executable and selected installer artifact are rediscovered from the second run only, with no stale sidecar/bundle ambiguity;
- `desktop/tests/build_idempotency.md` records the exact mode, commands, artifact evidence, and whether MSI was externally unavailable;
- prior M9 MSI evidence remains intact and is not represented as a fresh M11 MSI build.

---

## M11-BUILD-034 — Release Executable Local Smoke

### Dependencies

`M11-BUILD-033`

### Owned Files

```text
desktop/tests/release_executable_smoke.md
backend/tests/packaging/test_packaged_sidecar_contract.py
```

### Implementation

Automate the maximum non-GUI smoke possible for the release build and packaged sidecar without launching live Codex: file presence, PE/process launch where safe, sidecar handshake/health/status, and clean termination.

### Acceptance

Release executable/sidecar smoke evidence passes without manual UI claims.

---

## M11-GATE-035 — Release Candidate Automated Gate

### Dependencies

`M11-BUILD-034`

### Owned Files

```text
backend/**
frontend/**
desktop/**
scripts/**
docs/rc-validation-contract.md
```

### Implementation

Run M10 regression plus all M11 RC suites, path/restart/complex-workflow/desktop/build checks. Bounded repairs allowed inside frozen architecture; no network/live Codex/manual GUI.

### Acceptance

All M11 automated RC gates pass with no unsupported manual claims.

---

## M11-REPORT-036 — Release Candidate Report

### Dependencies

`M11-GATE-035`

### Owned Files

```text
docs/release-candidate-test-report.md
```

### Implementation

Record exact M11 commands/results, resolved remediations, remaining manual checks, and confirm no new external dependency was introduced. On PASS advance to M12-UX-001.

### Acceptance

M11 report is complete and evidence-backed; M12 becomes next.

---


# M12 — Product Quality / Operations

## Goal

Make the release candidate easier to start, move, inspect, diagnose and operate: starter workflows, definition import/export, redacted diagnostics, safe database backup, scalable run history, clearer runtime UX, accessibility and large-data UI guards.

## Frozen boundaries

- No scheduler semantic changes.
- No restore-in-place feature while the application is running; M12 backup is export-only.
- Workflow import/export transfers definitions only, never run/attempt/event history.
- Diagnostics are explicit user actions and use an allowlist/redaction model.
- No new UI framework or third-party dependency.
- No automatic file-system scanning, telemetry, cloud upload, or background network access.

## Deterministic Task Order

```text
M12-UX-001
↓
M12-SAMPLE-002
↓
M12-SAMPLE-003
↓
M12-ONBOARD-004
↓
M12-ONBOARD-005
↓
M12-ONBOARD-006
↓
M12-EXPORT-007
↓
M12-EXPORT-008
↓
M12-EXPORT-009
↓
M12-IMPORT-010
↓
M12-IMPORT-011
↓
M12-IMPORT-012
↓
M12-IMPORT-013
↓
M12-IMPORT-014
↓
M12-IMPORT-015
↓
M12-DIAG-016
↓
M12-DIAG-017
↓
M12-DIAG-018
↓
M12-DIAG-019
↓
M12-DIAG-020
↓
M12-DIAG-021
↓
M12-BACKUP-022
↓
M12-BACKUP-023
↓
M12-BACKUP-024
↓
M12-HISTORY-025
↓
M12-HISTORY-026
↓
M12-HISTORY-027
↓
M12-EVENT-028
↓
M12-EVENT-029
↓
M12-STATUS-030
↓
M12-STATUS-031
↓
M12-UX-032
↓
M12-UX-033
↓
M12-A11Y-034
↓
M12-PERF-035
↓
M12-PERF-036
↓
M12-GATE-037
↓
M12-REPORT-038
```

Execute exactly in order unless a genuine blocker occurs. Bounded remediation follows AGENTS.md and .codex/AUTO_EXECUTION.md and is not a reason to stop.

---

## M12-UX-001 — Productization Contract

### Dependencies

`M11-REPORT-036`

### Owned Files

```text
docs/productization-contract.md
```

### Implementation

Freeze M12 usability/operations scope: no scheduler redesign, no new third-party runtime dependency, no cloud/multi-user, no live Codex requirement, no network dependency. Define import/export, diagnostics, backup, history, onboarding and accessibility boundaries.

### Acceptance

Contract is explicit enough that later tasks require no product-policy guessing.

---

## M12-SAMPLE-002 — Canonical Sample Workflows

### Dependencies

`M12-UX-001`

### Owned Files

```text
frontend/src/samples/workflows.ts
frontend/src/samples/workflows.test.ts
```

### Implementation

Define a small set of deterministic starter workflows using the existing WorkflowDefinition schema: linear, fork/join, and continuation example. Prompts must be safe illustrative placeholders and not execute automatically.

### Acceptance

Samples validate against existing graph rules and contain no machine-specific cwd.

---

## M12-SAMPLE-003 — Sample Workflow Materialization

### Dependencies

`M12-SAMPLE-002`

### Owned Files

```text
frontend/src/samples/materialize.ts
frontend/src/samples/materialize.test.ts
```

### Implementation

Materialize a chosen sample into a new workflow with fresh deterministic/user-triggered ID generation and a user-selected/default cwd placeholder. Preserve all schema invariants.

### Acceptance

Materialized samples are valid and never overwrite an existing workflow id silently.

---

## M12-ONBOARD-004 — First-run Empty State

### Dependencies

`M12-SAMPLE-003`

### Owned Files

```text
frontend/src/features/workflows/WorkflowListPage.tsx
frontend/src/features/workflows/WorkflowListPage.test.tsx
frontend/src/features/workflows/workflows.css
```

### Implementation

When no workflows exist, show concise first-run guidance with Create workflow and Try sample actions. Do not add modal frameworks or external assets.

### Acceptance

Empty-state tests pass and existing non-empty list behavior is unchanged.

---

## M12-ONBOARD-005 — Sample Picker

### Dependencies

`M12-ONBOARD-004`

### Owned Files

```text
frontend/src/features/workflows/SampleWorkflowPicker.tsx
frontend/src/features/workflows/SampleWorkflowPicker.test.tsx
frontend/src/features/workflows/workflows.css
```

### Implementation

Provide an accessible picker for the canonical samples, describing topology and purpose before creation.

### Acceptance

Picker keyboard/selection/cancel tests pass.

---

## M12-ONBOARD-006 — Create Sample & Open Editor

### Dependencies

`M12-ONBOARD-005`

### Owned Files

```text
frontend/src/features/workflows/WorkflowListPage.tsx
frontend/src/features/workflows/SampleWorkflowPicker.tsx
frontend/src/features/workflows/WorkflowListPage.test.tsx
```

### Implementation

Wire sample materialization through the existing WorkflowApi create path, then navigate to the editor. No direct storage writes from frontend.

### Acceptance

Created sample appears via API and editor navigation uses the returned workflow id.

---

## M12-EXPORT-007 — Canonical Workflow Export Serializer

### Dependencies

`M12-ONBOARD-006`

### Owned Files

```text
backend/src/codex_flow/application/workflow_transfer.py
backend/tests/unit/test_workflow_export.py
```

### Implementation

Serialize one WorkflowDefinition to a versioned JSON envelope with stable field ordering/format and no run/task/attempt/event state.

### Acceptance

Export round-trip source data is deterministic and contains definition data only.

---

## M12-EXPORT-008 — Workflow Export API

### Dependencies

`M12-EXPORT-007`

### Owned Files

```text
backend/src/codex_flow/api/routes/workflows.py
backend/src/codex_flow/api/schemas.py
backend/tests/api/test_workflow_export.py
```

### Implementation

Expose GET /api/workflows/{id}/export returning the versioned transfer envelope via existing application/storage layers.

### Acceptance

Export endpoint handles success/not-found with stable schema and no SDK objects.

---

## M12-EXPORT-009 — Workflow Export UI

### Dependencies

`M12-EXPORT-008`

### Owned Files

```text
frontend/src/api/client.ts
frontend/src/features/workflows/WorkflowListPage.tsx
frontend/src/features/workflows/WorkflowEditorPage.tsx
frontend/src/features/workflows/WorkflowExportButton.tsx
frontend/src/features/workflows/WorkflowExportButton.test.tsx
```

### Implementation

Add explicit Export action that downloads a JSON file using browser/Tauri-compatible Blob APIs. Filename must be sanitized and deterministic.

### Acceptance

Export UI tests verify endpoint use, filename sanitization and no mutation.

---

## M12-IMPORT-010 — Workflow Import Parser

### Dependencies

`M12-EXPORT-009`

### Owned Files

```text
backend/src/codex_flow/application/workflow_transfer.py
backend/tests/unit/test_workflow_import.py
```

### Implementation

Parse the versioned export envelope, reject unsupported versions/malformed fields, and validate through WorkflowDefinition plus canonical graph validation.

### Acceptance

Malformed/unsupported/cyclic imports fail visibly; valid exports parse exactly.

---

## M12-IMPORT-011 — Import Identity Policy

### Dependencies

`M12-IMPORT-010`

### Owned Files

```text
backend/src/codex_flow/application/workflow_transfer.py
backend/tests/unit/test_workflow_import.py
```

### Implementation

Define deterministic import identity behavior: preserve id only when unused; otherwise require explicit replacement/new-id behavior supplied by request, never silent overwrite.

### Acceptance

Conflict matrix is deterministic and unit-tested.

---

## M12-IMPORT-012 — Workflow Import API

### Dependencies

`M12-IMPORT-011`

### Owned Files

```text
backend/src/codex_flow/api/routes/workflows.py
backend/src/codex_flow/api/schemas.py
backend/tests/api/test_workflow_import.py
```

### Implementation

Expose POST /api/workflows/import through application service with stable validation/conflict errors and no direct SQL in route code.

### Acceptance

Valid import persists one definition; conflicts/malformed data return stable errors.

---

## M12-IMPORT-013 — Frontend Import Client

### Dependencies

`M12-IMPORT-012`

### Owned Files

```text
frontend/src/api/types.ts
frontend/src/api/client.ts
frontend/src/features/workflows/api.ts
frontend/src/features/workflows/api.test.ts
```

### Implementation

Add typed import request/result methods matching the backend transfer contract.

### Acceptance

Typed client mapping/error tests pass.

---

## M12-IMPORT-014 — Workflow Import UI

### Dependencies

`M12-IMPORT-013`

### Owned Files

```text
frontend/src/features/workflows/WorkflowImportDialog.tsx
frontend/src/features/workflows/WorkflowImportDialog.test.tsx
frontend/src/features/workflows/WorkflowListPage.tsx
frontend/src/features/workflows/workflows.css
```

### Implementation

Allow user-selected JSON file import, preview name/task count, show validation/conflict errors, and navigate to imported editor on success. No automatic file-system scanning.

### Acceptance

File/preview/error/success keyboard tests pass.

---

## M12-IMPORT-015 — Import/Export Round-trip Matrix

### Dependencies

`M12-IMPORT-014`

### Owned Files

```text
backend/tests/integration/test_workflow_transfer_roundtrip.py
frontend/src/features/workflows/WorkflowImportDialog.test.tsx
```

### Implementation

Round-trip linear/fork-join/continuation definitions through export->import, including Unicode prompts and whitespace preservation.

### Acceptance

Definitions round-trip without semantic/prompt whitespace loss.

---

## M12-DIAG-016 — Diagnostic Summary Model

### Dependencies

`M12-IMPORT-015`

### Owned Files

```text
backend/src/codex_flow/application/diagnostics.py
backend/tests/unit/test_diagnostics.py
```

### Implementation

Define an SDK-independent diagnostic summary containing app/backend version, OS/Python info, DB schema version/path category, runtime active counts, recent non-sensitive error event types, and log directory category. Never include prompts/tokens/content bodies.

### Acceptance

Diagnostic model/redaction unit matrix passes.

---

## M12-DIAG-017 — Diagnostic Service

### Dependencies

`M12-DIAG-016`

### Owned Files

```text
backend/src/codex_flow/application/diagnostics.py
backend/tests/integration/test_diagnostics_service.py
```

### Implementation

Gather the diagnostic summary from repositories/runtime/config with explicit redaction and bounded recent metadata. Fail visibly when optional facts are unavailable rather than guessing.

### Acceptance

Service produces useful bounded metadata with no secrets or prompt text.

---

## M12-DIAG-018 — Diagnostics API

### Dependencies

`M12-DIAG-017`

### Owned Files

```text
backend/src/codex_flow/api/routes/system.py
backend/src/codex_flow/api/schemas.py
backend/tests/api/test_diagnostics_api.py
```

### Implementation

Expose authenticated GET /api/system/diagnostics using the diagnostic service, respecting existing desktop token rules.

### Acceptance

Authorized diagnostics succeeds; unauthorized desktop request fails; response is redacted.

---

## M12-DIAG-019 — Diagnostic Bundle Export

### Dependencies

`M12-DIAG-018`

### Owned Files

```text
backend/src/codex_flow/application/diagnostic_bundle.py
backend/tests/integration/test_diagnostic_bundle.py
```

### Implementation

Create a user-triggered ZIP bundle using Python stdlib zipfile containing diagnostic JSON, bounded redacted logs, schema/version metadata, and artifact manifest if present. Do not include the SQLite DB, prompts, tokens or environment dump.

### Acceptance

ZIP content allowlist/redaction tests pass and bundle is reproducible enough for inspection.

---

## M12-DIAG-020 — Diagnostic Bundle API

### Dependencies

`M12-DIAG-019`

### Owned Files

```text
backend/src/codex_flow/api/routes/system.py
backend/tests/api/test_diagnostic_bundle_api.py
```

### Implementation

Expose a user-triggered diagnostics bundle download endpoint. Bundle generation must occur only on request and use existing token protection.

### Acceptance

Download has correct content type/name and contains only allowlisted files.

---

## M12-DIAG-021 — Diagnostics UI

### Dependencies

`M12-DIAG-020`

### Owned Files

```text
frontend/src/api/client.ts
frontend/src/features/system/DiagnosticsPanel.tsx
frontend/src/features/system/DiagnosticsPanel.test.tsx
frontend/src/app/AppShell.tsx
```

### Implementation

Add a simple Diagnostics view showing summary metadata and Download diagnostic bundle action. No raw token/path secrets displayed.

### Acceptance

Diagnostics view/download/error tests pass.

---

## M12-BACKUP-022 — SQLite Online Backup Service

### Dependencies

`M12-DIAG-021`

### Owned Files

```text
backend/src/codex_flow/application/backup.py
backend/tests/integration/test_database_backup.py
```

### Implementation

Use SQLite's backup API to create a consistent user-requested backup while reads/runtime may exist. Backup goes to an explicit temporary/output path and never mutates source DB.

### Acceptance

Backup opens cleanly and contains a consistent schema/workflow/run snapshot.

---

## M12-BACKUP-023 — Database Backup API

### Dependencies

`M12-BACKUP-022`

### Owned Files

```text
backend/src/codex_flow/api/routes/system.py
backend/tests/api/test_database_backup_api.py
```

### Implementation

Expose authenticated user-triggered database backup download. Do not implement restore in M12; avoid dangerous in-place replacement while app is running.

### Acceptance

Backup endpoint returns a valid SQLite copy and preserves source DB.

---

## M12-BACKUP-024 — Backup UI

### Dependencies

`M12-BACKUP-023`

### Owned Files

```text
frontend/src/api/client.ts
frontend/src/features/system/DiagnosticsPanel.tsx
frontend/src/features/system/DiagnosticsPanel.test.tsx
```

### Implementation

Add explicit Download database backup action with a warning that backups contain workflow/run data and should be stored securely.

### Acceptance

Backup action/error tests pass and no automatic backups/downloads occur.

---

## M12-HISTORY-025 — Run History Pagination Backend

### Dependencies

`M12-BACKUP-024`

### Owned Files

```text
backend/src/codex_flow/storage/repositories.py
backend/src/codex_flow/application/runs.py
backend/src/codex_flow/api/routes/runs.py
backend/src/codex_flow/api/schemas.py
backend/tests/api/test_run_pagination.py
```

### Implementation

Add stable cursor/limit pagination for run history while preserving existing default list behavior for current clients. Ordering must be deterministic by created_at plus id.

### Acceptance

Pagination has no duplicates/gaps across pages and existing list callers remain compatible.

---

## M12-HISTORY-026 — Run History Pagination Frontend

### Dependencies

`M12-HISTORY-025`

### Owned Files

```text
frontend/src/api/types.ts
frontend/src/api/client.ts
frontend/src/features/runs/api.ts
frontend/src/features/runs/RunListPage.tsx
frontend/src/features/runs/RunListPage.test.tsx
```

### Implementation

Consume paginated run history with explicit Load more control while retaining current initial experience.

### Acceptance

Pagination UI appends without duplicate runs and handles end/error states.

---

## M12-HISTORY-027 — Run History Filters & Search

### Dependencies

`M12-HISTORY-026`

### Owned Files

```text
frontend/src/features/runs/RunListPage.tsx
frontend/src/features/runs/RunListPage.test.tsx
frontend/src/features/runs/runs.css
```

### Implementation

Add local filters for status and workflow/name/id text over loaded history. Do not change scheduler/storage semantics.

### Acceptance

Filter/search/clear tests pass and do not mutate backend state.

---

## M12-EVENT-028 — Event Log Filtering

### Dependencies

`M12-HISTORY-027`

### Owned Files

```text
frontend/src/features/runs/EventLog.tsx
frontend/src/features/runs/EventLog.test.tsx
frontend/src/features/runs/runs.css
```

### Implementation

Add event-type/task text filters and a clear/reset affordance to the existing event log while preserving chronological display.

### Acceptance

Filter matrix passes and original event order is unchanged.

---

## M12-EVENT-029 — Safe Copy Event Details

### Dependencies

`M12-EVENT-028`

### Owned Files

```text
frontend/src/features/runs/EventLog.tsx
frontend/src/features/runs/EventLog.test.tsx
```

### Implementation

Add explicit Copy details for displayed redacted event metadata only. Do not expose hidden token/prompt fields; fall back visibly if clipboard API is unavailable.

### Acceptance

Clipboard success/failure/redaction tests pass.

---

## M12-STATUS-030 — Runtime/About Public Model

### Dependencies

`M12-EVENT-029`

### Owned Files

```text
backend/src/codex_flow/api/routes/system.py
backend/src/codex_flow/api/schemas.py
backend/tests/api/test_about_status.py
```

### Implementation

Expose stable app/backend version, DB schema version, desktop_mode and high-level runtime availability/active count. No secrets, filesystem internals beyond safe category labels, or SDK private data.

### Acceptance

About/status API is authenticated in desktop mode and redacted.

---

## M12-STATUS-031 — About & Runtime Status UI

### Dependencies

`M12-STATUS-030`

### Owned Files

```text
frontend/src/api/client.ts
frontend/src/features/system/AboutPage.tsx
frontend/src/features/system/AboutPage.test.tsx
frontend/src/app/router.tsx
frontend/src/app/AppShell.tsx
```

### Implementation

Add lightweight About/Runtime view showing version and whether local backend is available, with link/navigation to Diagnostics.

### Acceptance

About/status loading/success/error tests pass.

---

## M12-UX-032 — Task Drawer Action Clarity

### Dependencies

`M12-STATUS-031`

### Owned Files

```text
frontend/src/features/runs/TaskRunDrawer.tsx
frontend/src/features/runs/RunControls.tsx
frontend/src/features/runs/TaskRunDrawer.test.tsx
frontend/src/features/runs/RunControls.test.tsx
```

### Implementation

Review control labels/help text for Retry/Cancel/Skip/Mark Success/Attention states so consequences are explicit. No new control semantics.

### Acceptance

UX tests confirm correct actions/states and destructive confirmations remain intact.

---

## M12-UX-033 — Desktop Startup Recovery Guidance

### Dependencies

`M12-UX-032`

### Owned Files

```text
frontend/src/desktop/DesktopStartupGate.tsx
frontend/src/desktop/DesktopStartupGate.test.tsx
frontend/src/desktop/DesktopStartupGate.css
```

### Implementation

Improve failure copy to distinguish retryable local-backend startup from persistent failure and point to Diagnostics/log location category without exposing paths/tokens. Keep retry behavior bounded.

### Acceptance

Startup recovery states remain deterministic and accessible.

---

## M12-A11Y-034 — Keyboard/Focus/Accessibility Regression

### Dependencies

`M12-UX-033`

### Owned Files

```text
frontend/src/app/**
frontend/src/features/**
frontend/src/desktop/**
```

### Implementation

Run a focused accessibility pass using existing test stack only: keyboard-reachable primary actions, dialog focus restore, meaningful labels, no obvious duplicate ids, status/error roles. Repair bounded issues without a new accessibility package.

### Acceptance

Focused accessibility regression passes across workflow/editor/run/import/diagnostics/startup flows.

---

## M12-PERF-035 — Large DAG UI Performance Guard

### Dependencies

`M12-A11Y-034`

### Owned Files

```text
frontend/src/features/editor/**
frontend/src/features/runs/**
```

### Implementation

Add deterministic performance-oriented regression using a 100-node fixture: mapping/validation/render-state transformations must remain bounded and not trigger accidental quadratic repeated API calls. Avoid fragile wall-clock thresholds; assert operation counts where possible.

### Acceptance

100-node UI fixture behaves correctly with bounded call/update counts.

---

## M12-PERF-036 — Large History/Event UI Guard

### Dependencies

`M12-PERF-035`

### Owned Files

```text
frontend/src/features/runs/**
```

### Implementation

Exercise hundreds of runs and thousands of event fixture entries through pagination/filter components, asserting bounded fetches, stable ordering and no duplicate rendered keys.

### Acceptance

Large fixture regression passes without unbounded reconnect/fetch/render loops.

---

## M12-GATE-037 — Productization Automated Gate

### Dependencies

`M12-PERF-036`

### Owned Files

```text
backend/**
frontend/**
desktop/**
scripts/**
docs/productization-contract.md
```

### Implementation

Run all M10/M11 regressions plus M12 sample/import/export/diagnostics/backup/history/UX/accessibility/performance tests, frontend typecheck/lint/build, backend Ruff/mypy, Rust/Tauri checks. No live Codex/network/manual GUI.

### Acceptance

Complete productization gate passes with bounded remediation only.

---

## M12-REPORT-038 — Productization Report & Manual Handoff

### Dependencies

`M12-GATE-037`

### Owned Files

```text
docs/productization-test-report.md
docs/manual-v1-checklist.md
README.md
```

### Implementation

Record exact M12 evidence, refresh README from outdated early-headless wording, and produce final manual checklist for installer launch, native notification appearance, Open-in-Codex, real Codex workflow, and subjective UI review. Set next_task null after PASS.

### Acceptance

M12 report/README/manual checklist accurately describe a release-candidate local desktop product and distinguish automated from manual evidence.

---

