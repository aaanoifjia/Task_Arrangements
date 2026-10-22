# Codex Flow — Current Progress

Updated: 2026-10-22

## Current Phase

M11 — Release Candidate / Real-world Validation.

M7 Visual DAG UI is complete with all automated gates PASS. The authoritative late-phase plans define the completed M8–M10 reliability, packaging, and hardening work, followed by 74 deterministic M11–M12 release-candidate and product-quality tasks.

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
- M9-DESKTOP-010 — real PyInstaller sidecar build, packaged help/version smoke, and migration resource verification PASS; packaging tests 2/2 and Ruff PASS; bounded remediation R1 complete
- M9-DESKTOP-011 — Tauri externalBin configuration for Windows sidecar; Tauri config/schema validation and cargo metadata PASS
- M9-DESKTOP-036 — packaged sidecar handshake, healthz, authenticated system status, and clean termination contract; packaging tests 3/3 and Ruff PASS; PyInstaller `_internal` runtime staging repaired in the owned desktop build script
- M9-DESKTOP-037 — automated desktop integration harness for sidecar lifecycle, runtime state, auth token, app-data paths, crash/relaunch, and frontend bridge; Tauri cargo test 25/25, focused frontend desktop tests 8/8, typecheck, and ESLint PASS; bounded remediation M9-DESKTOP-037-R1 generated the reproducible temporary engineering icon set through the official Tauri CLI
- M9-DESKTOP-038 — Windows frontend, PyInstaller sidecar, Tauri release executable, MSI bundle, and NSIS installer all PASS; exact artifact filenames, sizes, and SHA256 hashes recorded in `docs/windows-build-artifacts.md`
- M9-GATE-039 — automated M9 gate PASS; backend non-live 257 passed/6 deselected, frontend 52 files/173 tests with typecheck/lint/build, Tauri 25/25 plus cargo check, PyInstaller/Tauri/MSI/NSIS bundles, strict mypy, and token/log/path security scans
- M9-REPORT-040 — automated M9 desktop packaging report PASS; exact sidecar, bundle, runtime, path, auth-home, token-security, notification, Open-in-Codex, and regression evidence recorded; manual Desktop checks explicitly deferred
- M10-HARDEN-001 — runtime parity audit PASS; 2 direct parity checks passed, 3 strict xfails identify only known continuation/parallelism/timeout gaps, related runtime/scheduler regression 33 passed, and the bounded gap map is recorded in `docs/runtime-parity-audit.md`
- M10-HARDEN-002 — durable CONTINUE_THREAD PASS; successful source thread is resumed with no new source thread and a distinct new turn persisted; continuation/runtime regression 30 passed with 2 known-gap xfails, plus Ruff and strict mypy
- M10-HARDEN-003 — continuation Attempt persistence PASS; STARTING plus one Attempt is committed before external resume, same source thread/new turn refs are recorded, transaction/ref tests 5 passed, regression 12 passed, and Ruff/strict mypy passed
- M10-HARDEN-004 — continuation recovery safety PASS; four crash points fail closed without resending prompts or releasing downstream work, matrix 6 passed and recovery regression 15 passed
- M10-HARDEN-005 — global concurrency configuration PASS; default one, non-positive rejection, and runtime wiring passed 11 tests; full backend non-live 271 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed
- M10-HARDEN-006 — parallel READY execution PASS; independent delayed tasks overlap at limit 2 and serialize at limit 1 with deterministic A→B selection; full backend non-live 274 passed/6 deselected/2 known xfailed and Ruff passed
- M10-HARDEN-007 — durable workspace lock PASS; same-cwd writes serialize and different-cwd writes overlap under the global limit; workspace matrix 9 passed, full backend non-live 276 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed
- M10-HARDEN-008 — durable thread-turn lock PASS; same-thread continuation turns serialize with shared thread identity; full backend non-live 277 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed
- M10-HARDEN-009 — persistent fork/join PASS; database-backed A→B/C→D overlaps B/C and releases D only after both complete; focused 7 passed, full backend non-live 278 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed
- M10-HARDEN-010 — same-workspace fork serialization PASS; B/C peak=1 and D starts only after both complete; focused 4 passed, full backend non-live 279 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed
- M10-HARDEN-011 — cross-run global capacity PASS; simultaneous workflows shared one RuntimeManager limiter; focused cross-run/workspace tests 3 passed, full backend non-live 281 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed
- M10-HARDEN-012 — transient error classification PASS; only explicit server-busy, transport-overload, disconnect, and reset signals are retryable; classification table 13 passed, Ruff and strict mypy passed
- M10-HARDEN-013 — deterministic retry backoff PASS; bounded exponential sequence/cap and injectable sleeper tests 12 passed, Ruff and strict mypy passed
- M10-HARDEN-014 — automatic server-busy retry PASS; explicit SERVER_BUSY retried within max_attempts with distinct Attempts and audit; focused regression 5 passed/2 known xfailed, full backend non-live 307 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed
- M10-HARDEN-015 — automatic transport retry PASS; explicit transient disconnect before TURN_STARTED retried safely while ambiguous external start remained STARTING without retry; focused tests 3 passed, full backend non-live 309 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed
- M10-HARDEN-016 — no automatic retry for task failure PASS; tool/task failure, permission/validation attention, interrupt, and unknown adapter failure matrix 6 passed; full backend non-live 315 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed
- M10-HARDEN-017 — max-attempts enforcement PASS; persistent SERVER_BUSY stopped exactly at max_attempts=3 with parent NEEDS_ATTENTION, child BLOCKED, and retry audits; focused test, Ruff, and strict mypy passed
- M10-HARDEN-018 — retry audit trail PASS; ordered AUTO_RETRY_SCHEDULED/RETRY_REQUESTED/AUTO_RETRY_EXHAUSTED events carry attempt numbers and secret-free reason classes; focused audit suite 4 passed, full backend non-live 318 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed
- M10-HARDEN-019 — task timeout enforcement PASS; timeout interrupted one hanging turn, persisted INTERRUPTED plus TASK_TIMEOUT, and left the child BLOCKED; focused timeout test passed, full backend non-live 319 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed
- M10-HARDEN-020 — timeout vs terminal race PASS; terminal-before-timeout and timeout-before-late-terminal matrix 2 passed, with compare-and-update preventing late overwrite; full backend non-live 321 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed
- M10-HARDEN-021 — timeout restart recovery PASS; timeout/interrupt restart matrix and continuation recovery 6 passed, no-thread crashes failed closed, referenced threads were only read, descendants remained BLOCKED; full backend non-live 323 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed
- M10-HARDEN-022 — SQLite busy timeout and WAL guard PASS; WAL, foreign_keys, 5000ms busy_timeout, and concurrent short-lock write test 2 passed; full backend non-live 325 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed
- M10-HARDEN-023 — storage query index migration PASS; migration 0003 indexes, fresh/v1/v2 upgrade/idempotence, and query-plan assertions passed; migration/API compatibility suite 10 passed, full backend non-live 328 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed; bounded remediation M10-HARDEN-023-R1 synchronized three directly implicated v2 assertions
- M10-HARDEN-024 — large DAG determinism PASS; deterministic 100-node mixed chain/fork/join DAG ran twice with identical start/completion order, all tasks SUCCESS, and one Attempt each; stress test passed, full backend non-live 329 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed
- M10-HARDEN-025 — high event volume PASS; 5,000 persisted events delivered through 127-event cursor batches with no duplication/loss across 40 bounded polls; event-volume suite 4 passed, full backend non-live 330 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed
- M10-HARDEN-026 — WebSocket reconnect storm PASS; backend reconnect stress 3 passed, frontend targeted reconnect/dedupe 7 passed, full frontend 52 files/174 tests with typecheck/lint, and full backend non-live 331 passed/6 deselected/2 known xfailed; cursor resume produced no duplicate events
- M10-HARDEN-027 — concurrent API read/control stress PASS; stable allowed responses, valid task/run states, and JSON audit payloads under concurrent controls; focused stress passed, full backend non-live 332 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed
- M10-HARDEN-028 — crash fault matrix expansion PASS; deterministic crash fault plus duplicate/continuation recovery 17 passed, ambiguous states failed closed, descendants stayed BLOCKED, and no external create/start/resume repeated; full backend non-live 340 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed
- M10-HARDEN-029 — duplicate-prevention property matrix PASS; deterministic success, tool failure, interrupt, terminal failure, attention, stream crash, and manual retry scenarios 7 passed, each Attempt had one external prompt, and non-SUCCESS parents kept children BLOCKED; full backend non-live 347 passed/6 deselected/2 known xfailed, Ruff and strict mypy passed
- M10-HARDEN-030 — frontend degraded backend recovery PASS; temporary 503, malformed response, WebSocket loss/reconnect, and backend restart retry matrix 18 passed; full frontend 52 files/177 tests, typecheck, and ESLint passed
- M10-HARDEN-031 — desktop sidecar restart soak PASS; deterministic eight-cycle Fake sidecar start/crash/relaunch matrix reused one app-data DB path, generated unique restart identities, rejected relaunch loops, cleaned child processes, and full Tauri Rust tests passed 26/26; Cargo fmt was unavailable because rustfmt is not installed in the existing toolchain
- M10-HARDEN-032 — accelerated long-run soak PASS; Fake workflow soak covered 24 deterministic mixed success/tool-failure iterations with no leaked runtime tasks, no active runs, and consistent attempts/events; frontend reconnect soak covered 100 cursor-resumed reconnects with dedupe; full backend non-live 348 passed/6 deselected/2 known xfailed, full frontend 52 files/177 tests, typecheck, and ESLint passed
- M10-HARDEN-033 — full product regression PASS; backend non-live 348 passed/6 deselected/2 known xfailed, frontend 52 files/177 tests with typecheck/lint/production build, packaging contract 3 passed, Tauri cargo check plus 26 Rust tests, and Ruff passed
- M10-HARDEN-034 — v1 acceptance evidence matrix PASS; all 22 acceptance items map to existing automated/manual evidence, all referenced paths were verified, and manual-only/both-mode UX items remain explicitly PENDING
- M10-GATE-035 — final automated M10 beta gate PASS; backend non-live 348 passed/6 deselected/2 known xfailed, packaging plus stress 22 passed, frontend 52 files/177 tests with typecheck/lint/build, and Tauri cargo check plus 26 tests; live Codex and manual UX remain excluded by design
- M10-REPORT-036 — M10 automated hardening report PASS; exact automated results recorded, all 22 v1 acceptance items mapped, and final manual V1 checklist created with Desktop/UI observations explicitly pending
- M11-RC-001 — offline release-candidate contract and local toolchain/Tauri-input preflight PASS; 2 tests and Ruff passed without installation or download
- M11-FIXTURE-002 — deterministic app-data, workflow, Fake adapter, SQLite run, and process lifecycle fixture factory PASS; 5 tests and Ruff passed
- M11-PATH-003 — durable Fake workflow in a nested space-containing workspace PASS; exact cwd persistence, canonical lock serialization, and no duplicate execution verified; 5 related tests and Ruff passed
- M11-PATH-004 — durable Fake workflow under a Windows-safe Unicode workspace PASS; exact snapshot, canonical key, event persistence, terminal state, and cleanup verified; 6 related tests and Ruff passed
- M11-PATH-005 — deep workflow path with spaces and Unicode PASS; generated fixture files stayed under the intended root and below the Windows path limit; 7 related tests and Ruff passed
- M11-PATH-006 — missing cwd fail-visible behavior PASS; no fallback or downstream release, parent remained STARTING and child BLOCKED; 6 related tests and Ruff passed
- M11-DATA-007 — SQLite reopen matrix PASS; workflow/run/task/attempt identifiers, snapshots, statuses, controls, references, and event order survived reopen; 6 related tests and Ruff passed
- M11-DATA-008 — fresh/v1/v2/v3 migration rehearsal and reopen idempotence PASS; latest schema/indexes and historical data preserved; 9 related tests and Ruff passed
- M11-DATA-009 — event cursor restart PASS; resumed EventStream returned only later events in stable order with no loss or duplication; 5 related tests and Ruff passed
- M11-DATA-010 — Attempt history restart PASS; immutable IDs, statuses, thread/turn references, and ordering survived restart without overwrite; 5 related tests and Ruff passed
- M11-RECOVERY-011 — queued run restart PASS; pre-turn recreation stayed fail-closed with no external call/child release, replacement runner executed each task once; 8 related tests and Ruff passed
- M11-RECOVERY-012 — paused run restart PASS; no start before explicit Resume, one resumed execution, and active work reconciled to NEEDS_ATTENTION; 10 related tests and Ruff passed
- M11-RECOVERY-013 — NEEDS_ATTENTION restart PASS; state remained actionable with one reconciliation event, no success conversion, and no prompt rerun; 11 related tests and Ruff passed
- M11-RECOVERY-014 — control/restart matrix PASS; pause/resume, queued/running cancel, skip, mark-success, retry, audit, and downstream readiness covered; 18 related tests and Ruff passed
- M11-RECOVERY-015 — multiple-run restart PASS; queued/active/attention workflows restored independently with isolated run/task/thread identities; 10 related tests and Ruff passed
- M11-WORKFLOW-016 — deterministic 20-node mixed DAG PASS; all tasks succeeded once with dependency-ordered starts, no premature joins, and exact continuation thread reuse; 7 related tests and Ruff passed
- M11-WORKFLOW-017 — mixed failure/recovery DAG PASS; pause/resume, skip blocking, retry release, Attempt history, audit, and deterministic FAILED outcome verified; 21 related tests and Ruff passed
- M11-WORKFLOW-018 — continuation chain PASS; exact source-thread reuse and isolated NEW_THREAD branches verified across 10 successful tasks; 10 related tests and Ruff passed
- M11-WORKFLOW-019 — independent workspace parallelism PASS; event-synchronized overlap at capacity 2 and deterministic final state verified; 9 related tests and Ruff passed
- M11-WORKFLOW-020 — equivalent same-workspace serialization PASS; peak overlap 1 and release-gated second start verified; 8 related tests and Ruff passed
- M11-WORKFLOW-021 — repeated run isolation PASS; distinct run/task/attempt/thread/turn identities and per-run events verified; 8 related tests and Ruff passed
- M11-WORKFLOW-022 — 50-run history durability PASS; complete stable run ordering, task/attempt lookups, identities, references, and events survived reopen; 7 related tests and Ruff passed

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

Current task:

`M11-LOG-030` — Crash Log Secret Redaction — IN_PROGRESS

M10 automated hardening is COMPLETE. M11–M12 are now authoritative and queued on master:

- M11: 36 release-candidate / real-world validation tasks;
- M12: 38 product-quality / operations tasks.

M11-RC-001 through M11-DESKTOP-029 are COMPLETE. M11-LOG-030 is now in progress; continue automatically through M12-REPORT-038.

M11/M12 are local/offline by default: no live Codex turn, external web research, new package downloads, or new system toolchains are required by the plan. Small deterministic adjacent integration failures should use bounded automatic remediation instead of stopping.

Subjective/manual Desktop verification remains intentionally deferred until M12-REPORT-038.
