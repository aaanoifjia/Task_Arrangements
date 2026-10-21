# Codex Flow — Current Progress

Updated: 2026-10-22

## Current Phase

M9 — Desktop Integration & Packaging.

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
- M8-CONTROL-029 — retry creates distinct immutable Attempts with fresh thread/turn references; identity integration, Ruff, and strict mypy PASS
- M8-CONTROL-030 — deterministic cancellation race matrix for queued, pre-turn, running, and late-terminal paths; 8/8 race tests PASS
- M8-UI-031A — repaired canonical frontend SKIPPED status mapping; focused status tests and `tsc -b` PASS
- M8-UI-031 — frontend run view model types; focused type tests and `tsc -b` PASS
- M8-UI-032A — typed low-level control ApiClient repair; endpoint/error tests 6/6 and `tsc -b` PASS
- M8-UI-032 — frontend RunApi control mappings; endpoint/error tests 2/2 and `tsc -b` PASS
- M8-UI-033 — durable-state-driven RunControls shell; visibility matrix 11/11, `tsc -b`, and ESLint PASS
- M8-UI-034 — pause/resume controls with pending/error feedback and durable refresh; focused tests 17/17, `tsc -b`, and ESLint PASS
- M8-UI-035 — explicit Retry for failed/interrupted/attention tasks; focused tests 22/22, `tsc -b`, and ESLint PASS
- M8-UI-036 — Cancel for allowed queued/active task states with pending feedback; focused tests 29/29, `tsc -b`, and ESLint PASS
- M8-UI-037 — Skip and Mark Success limited to canonical server-supported states; focused tests 34/34, `tsc -b`, and ESLint PASS
- M8-UI-038 — keyboard-accessible confirmation for Cancel/Skip/Mark Success; focused tests 20/20, `tsc -b`, and ESLint PASS
- M8-UI-039 — stable control feedback and 409 durable-state refresh; focused tests 22/22, `tsc -b`, and ESLint PASS
- M8-UI-040 — AttentionCenter NEEDS_ATTENTION aggregation/count/navigation; focused tests 3/3, `tsc -b`, and ESLint PASS
- M8-UI-041 — granted-only browser notification adapter with TaskRun-id dedupe; focused tests 4/4, `tsc -b`, and ESLint PASS
- M8-INTEGRATE-042 — full Fake human-in-the-loop integration and bounded v2 test-fixture repairs; backend non-live 235 passed, frontend 49 files/160 tests, `tsc -b`, ESLint, and production build PASS
- M8-GATE-043 — M8 reliability acceptance matrix; backend non-live 235 passed, frontend 49 files/160 tests, `tsc -b`, ESLint, and production build PASS
- M8-REPORT-044 — M8 human-in-the-loop reliability report with exact PASS evidence and deferred manual limits
- M9-DESKTOP-001 — Tauri v2/Python sidecar desktop runtime contract; contract consistency acceptance PASS
- M9-DESKTOP-002 — Tauri v2 API/CLI dependencies and desktop scripts; npm install, typecheck, lint, and build PASS
- M9-PREFLIGHT-003A — complete Windows/Tauri prerequisite audit; official Rustup stable installation authorized and verified; all declared prerequisites PASS
- M9-DESKTOP-003 — minimal Tauri v2 Windows shell scaffold; cargo metadata and Tauri config/capability schema parsing PASS
- M9-DESKTOP-004 — independent production uvicorn server entrypoint; argument parsing/no-import-side-effect tests 3/3, Ruff, and strict mypy PASS
- M9-DESKTOP-005 — desktop loopback binding guard; IPv4/IPv6 acceptance and wildcard/LAN rejection tests 8/8, Ruff, and strict mypy PASS
- M9-DESKTOP-006 — optional per-process bearer-token REST middleware with token-safe health; authorization matrix 3/3, existing system/lifecycle regression 3/3, Ruff, and strict mypy PASS
- M9-DESKTOP-007 — WebSocket query-token validation; valid/invalid/missing matrix 3/3, existing WebSocket regression 2/2, Ruff, and strict mypy PASS
- M9-DESKTOP-008 — post-bind sidecar readiness handshake; parser/stdout ordering/token-exclusion tests 9/9, Ruff, and strict mypy PASS
- M9-DESKTOP-009 — reproducible PyInstaller sidecar spec with migrations/openai-codex collection; command generation, py_compile, Ruff, and secret scan PASS

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

`M9-DESKTOP-010` — Sidecar Build Smoke

M8 is complete. M9-DESKTOP-001 and M9-DESKTOP-002 are complete. M9-DESKTOP-003 discovered that Rust/Cargo is missing.

The repository protocol now supports:

- bounded automatic remediation for small deterministic non-owned integration repairs;
- milestone toolchain preflight so missing prerequisites are detected together;
- system-level installation only for an exact named toolchain explicitly authorized by an authoritative task or the user's current invocation.

M9-PREFLIGHT-003A audits Python/Node/PyInstaller/Rust/MSVC/Windows SDK/WebView2/Git. If the current invocation explicitly authorizes Rust, it may install the official Rust toolchain only. Other missing system components remain genuine blockers.

M9-PREFLIGHT-003A through M9-DESKTOP-009 are complete. The complete declared Windows/Tauri prerequisite audit is recorded in `docs/m9-environment-preflight.md`; the authorized official Rustup stable toolchain is installed and verified. M9-DESKTOP-010 is the next dependency-ready task for the sidecar build smoke.
