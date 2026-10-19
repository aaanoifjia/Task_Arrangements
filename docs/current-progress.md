# Codex Flow — Current Progress

Updated: 2026-10-19

## Current Phase

Early headless core, entering the Codex-control compatibility gate.

The deterministic local core is implemented through graph validation, state transitions, dependency readiness, and concurrency/workspace locking. The real Codex SDK path now authenticates successfully and completes an actual thread/turn/workspace-write probe.

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

`M3-MANUAL-006`

The scheduler core passed 45 relevant unit tests, Ruff, and strict mypy. The next task adds explicit manual scheduler controls.
