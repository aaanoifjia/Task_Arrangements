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

The next deterministic task is:

`M1-CTRL-003`

Authoritative task specification:

`.codex/tasks/M1-CTRL-003.md`

The existing control probe has already demonstrated a real interrupted terminal event. The remaining known defect is resumed-turn response extraction:

```text
first turn = completed
second turn = completed
second_response = ""
resume_verified = false

interrupt_requested = true
interrupt_event_received = true
interrupt_terminal_status = interrupted
```

M1-CTRL-003 now has a formal Owned Files / Steps / Acceptance definition and is READY to execute.

## Waiting After M1-CTRL-003

If M1-CTRL-003 passes:

```text
M1-PACK-005
→ M1-DESKTOP-004 (manual user observation gate)
→ M1-REPORT-006
→ M2-INTERFACE-001
→ M2-FAKE-002 + M2-SDK-003
→ M2-CONTRACT-004
→ M3-SCHED-005
→ M3-MANUAL-006 + M3-CONTINUE-007
→ M3-TEST-008
→ M4 persistence/recovery
→ M5 headless end-to-end MVP
```

M1-DESKTOP-004 remains an intentional manual gate because Desktop thread/sidebar behavior must be observed by the user.

## Durable Progress Rule

Each small task is committed only after its acceptance checks pass.

Before implementation starts, Codex records the task as `IN_PROGRESS` in `.codex/progress.json` and creates the required progress checkpoint commit.

If quota/context ends during a task:

- earlier completed tasks remain committed;
- the current task remains recorded as active;
- local dirty files are preserved;
- the next session resumes the active task instead of selecting another task.

See `AGENTS.md` and `.codex/AUTO_EXECUTION.md`.
