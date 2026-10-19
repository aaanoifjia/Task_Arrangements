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

`M1-DESKTOP-004`

The frozen package probe built and ran successfully. The next task is the explicitly defined Desktop deep-link/sidebar observation gate.
