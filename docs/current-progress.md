# Codex Flow — Current Progress

Updated: 2026-10-20

## Current Phase

M8 — Human-in-the-loop & Reliability.

M7 Visual DAG UI is complete with all automated gates PASS. The authoritative late-phase task plan now defines 120 deterministic autonomous tasks across M8–M10: durable human controls and reliability, Windows Tauri/Python-sidecar desktop packaging, then real-world hardening and automated beta gates.

## Completed

- PREP-000 — repository/environment bootstrap
- M0-ARCH-001 — architecture contract
- M0-DOMAIN-002 — domain model specification
- M0-STATE-003 — TaskRun state machine specification
- M0-ADR-004 — ADR-001 through ADR-008
- M0-ACCEPT-005 — V1 acceptance contract
- M3-GRAPH-001 — models, DAG validation, deterministic topological ordering, cycle detection
- M3-STATE-002 — deterministic TaskRun transition service
- M3-READY-003 — dependency readiness calculation
- M3-LOCK-004 — global concurrency, workspace write locks, thread-turn locks
- M1-HOME-FIX-001 — repaired child-process home environment
- M1-AUTH-001 — SDK version and existing ChatGPT Plus authentication verified
- M1-RUN-002 — real Codex thread, turn, stream completion, workspace write, and exact output verification
- M1-CTRL-003 — resumed-thread context verification and real turn interruption
- M1-PACK-005 — frozen PyInstaller feasibility probe; executable SDK/account check passed
- M1-DESKTOP-004 — user-verified Desktop deep link, sidebar visibility, searchability, and project association
- M1-REPORT-006 — M1 compatibility gate report; all M2 hard gates PASS
- M2-INTERFACE-001 — SDK-independent async Codex adapter contract
- M2-FAKE-002 — deterministic offline adapter; 8 contract-focused tests passed
- M2-SDK-003 — official SDK adapter; live exact-file-write smoke test passed
- M2-CONTRACT-004 — shared adapter contract suite; fake contract test passed
- M3-SCHED-005 — deterministic async scheduler core with adapter boundary, capacity/workspace/thread locking, and fail-closed terminal handling
- M3-MANUAL-006 — explicit retry, cancel, skip, mark-success, pause, and resume controls with clear action results
- M3-CONTINUE-007 — validated successful-source existing-thread resume with a distinct new turn
- M3-INTEGRATE-008A — integrated pause/resume, retry/readiness, and scheduler-dispatched existing-thread execution
- M3-TEST-008 — deterministic scheduler matrix covering DAG, failure, retry, controls, locks, concurrency, continuation, and cycles
- M4-SCHEMA-001 — SQLite migration 0001 with durable workflow, run, attempt, event, and settings tables
- M4-REPO-002 — transactional SQLite repositories for definitions, runs, attempts, events, and active-run queries
- M4-SNAPSHOT-003 — immutable workflow-run definition snapshots
- M4-ATTEMPT-004 — transactional local Attempt/STARTING persistence before adapter calls
- M4-RECOVERY-005 — fail-closed startup reconciliation for uncertain active external executions
- M4-DUP-006 — crash-point duplicate-execution prevention matrix
- M5-CLI-001 — standard-library headless CLI command surface
- M5-EXAMPLES-002 — canonical linear, fork/join, failure, and continuation workflow fixtures
- M5-LINEAR-003 — real isolated A → B Codex execution with exact output verification
- M5-FAILMAP-004A — command-execution failure details and terminal-stream failure propagation
- M5-FORKJOIN-004 — real fork/join evidence plus repaired scheduler failure blocking validation
- M5-RUNNER-005A — durable headless runner integration, CLI run wiring, and fresh-process SDK thread reads
- M5-RESTART-005 — real subprocess kill/restart recovery without duplicate prompts or downstream execution
- M5-REPORT-006 — headless MVP gate report; all required results PASS
- M7-INTEGRATE-056 — complete mocked visual DAG user flow; frontend Vitest 45 files/111 tests, typecheck, ESLint, and production build PASS
- M7-GATE-057 — M7 acceptance matrix PASS; frontend gates and non-live backend regression 141 passed
- M7-REPORT-058 — Visual DAG UI milestone report; all M7 gates PASS
- M8-CONTROL-001 — SDK-independent durable control command/result contract; 14 tests, Ruff, and strict mypy PASS
- M8-CONTROL-002 — idempotent v1→v2 run-control pause metadata migration; migration regression 4/4 PASS
- M8-CONTROL-003 — transactional pause persistence and stale-state compare updates; repository/migration regression 8/8 PASS
- M8-CONTROL-004 — append-only accepted/rejected manual-action audit events; integration/repository regression 5/5 PASS
- M8-CONTROL-005 — transactional retry reset with preserved attempts and RETRY_REQUESTED audit; regression 10/10 PASS
- M8-CONTROL-006 — process-local active Codex turn registry with terminal/error cleanup; runtime regression 7/7 PASS
- M8-CONTROL-007 — durable pause checkpoint prevents new starts without interrupting active work; regression 6/6 PASS
- M8-CONTROL-008 — atomic terminal-vs-control compare guard; cancel race matrix and runtime regression 6/6 PASS
- M8-CONTROL-009 — durable runtime pause operation with audit and no active-turn interruption; regression 6/6 PASS
- M8-CONTROL-010 — durable runtime resume with unfinished-work continuation and duplicate-runner guard; regression 7/7 PASS
- M8-CONTROL-011 — runtime retry reopens failed run and preserves old Attempts while creating fresh scheduler Attempt; regression 12/12 PASS
- M8-CONTROL-012 — queued PENDING/BLOCKED/READY cancellation with canonical transition and no external execution; matrix 3/3 PASS
- M8-CONTROL-013 — running cancellation with one interrupt, attempt cancellation, and terminal-race protection; regression 7/7 PASS
- M8-CONTROL-014 — canonical SKIP operation with downstream blocking; regression 9/9 PASS
- M8-CONTROL-015 — READY→SUCCESS mark-success override with downstream readiness release and audit; regression 11/11 PASS
- M8-CONTROL-016 — deterministic NEEDS_ATTENTION cancel/retry controls without implicit success; regression 5/5 PASS
- M8-CONTROL-017 — control application service dispatch and stable error translation; matrix 24/24 PASS
- M8-CONTROL-018 — SDK-independent ManualActionResponse and durable RunControlState schemas; serialization matrix 17/17 PASS
- M8-CONTROL-019 — pause REST endpoint through ControlApplicationService with stable error envelopes; API tests, Ruff, and strict mypy PASS
- M8-CONTROL-020 — resume REST endpoint returning the durable continuation request; API tests, Ruff, and strict mypy PASS
- M8-CONTROL-021 — retry REST endpoint accepting public task ids and TaskRun ids; API tests, Ruff, and strict mypy PASS
- M8-CONTROL-022 — queued/running cancel REST endpoint with stable conflict mapping; API matrix, Ruff, and strict mypy PASS
- M8-CONTROL-023 — skip REST endpoint with stable invalid-state error; API tests, Ruff, and strict mypy PASS
- M8-CONTROL-024 — mark-success REST endpoint with explicit success transition and audit path; API tests, Ruff, and strict mypy PASS
- M8-CONTROL-025 — stable control API error matrix for not-found, conflict, invalid-state, unavailable, and interrupt paths; 4 tests, Ruff, and strict mypy PASS
- M8-CONTROL-026 — manual pause/retry/cancel audit events through durable ordered stream with cursor reconnect; integration test, Ruff, and strict mypy PASS
- M8-CONTROL-027 — restart restores active workflow snapshots without starting paused work; reconciliation/resume integration 2/2 PASS, Ruff, and strict mypy PASS
- M8-CONTROL-028 — failed-parent retry releases blocked descendants exactly once; dependency-release and retry regression 2/2 PASS

## Verified Codex Runtime

Canonical existing Windows home:

```text
C:\Users\Administrator
```

Authentication:

```text
openai-codex = 0.162.1
account_access_ok = true
plan_type = plus
```

Basic real execution:

```text
turn/started = observed
turn/completed = observed
completed_status = completed
output_verified = true
unexpected_files = []
```

## Current Task

Current deterministic next task:

`M8-CONTROL-029` — Retry Attempt Identity

The late-phase plan contains 120 sequential tasks:
- M8: 44 tasks
- M9: 40 tasks
- M10: 36 tasks

It is intentionally sized for a long autonomous run (roughly 7–9 hours at recent project velocity). Codex should continue through `M10-REPORT-036` unless a genuine blocker or actual host termination occurs.

All user/manual Desktop checks are deferred until after M10 automated completion so they do not interrupt autonomous execution.
