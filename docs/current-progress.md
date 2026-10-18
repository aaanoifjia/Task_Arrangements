# Codex Flow — Current Progress

Updated: 2026-10-19

## Current Phase

Early headless core.

The deterministic local core is substantially ahead of the original initial status: graph/domain models, state transitions, readiness calculation, and concurrency/workspace locking are all present in the repository.

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

## Current Blocker

The real Codex SDK execution probe does not reach thread creation.

Recorded error:

```text
TransportClosedError: Codex process closed stdout.
WARNING: proceeding, even though we could not create PATH aliases:
Could not find home directory
Error: Could not find home directory
```

Therefore the next task is:

`M1-HOME-FIX-001`

Task spec:
`.codex/tasks/M1-HOME-FIX-001.md`

## Blocked / Waiting

- M1-RUN-002 — blocked by home-directory runtime failure
- M1-CTRL-003 — blocked until a real first turn can run
- M1-DESKTOP-004 — later manual user-observation gate
- M2 Adapter work — waits for M1 compatibility gate
- M3-SCHED-005 — local readiness/lock prerequisites are done, but it also waits for M2 Adapter contract

## Planned Automatic Sequence

After the home fix, follow `.codex/progress.json.next_task` and the recorded queue.

The intended near-term sequence is:

```text
M1-HOME-FIX-001
→ M1-AUTH-001
→ M1-RUN-002
→ M1-CTRL-003
→ M1-PACK-005
→ M1-DESKTOP-004 (manual user check)
→ M1-REPORT-006
→ M2 Adapter tasks
→ M3 Scheduler core
→ M4 persistence/recovery
→ M5 headless end-to-end MVP
```

## Durable Progress Rule

Each small task is committed only after its acceptance checks pass.

Before implementation starts, Codex first commits an `IN_PROGRESS` checkpoint to `.codex/progress.json`.

If quota ends during a task:
- earlier completed tasks are already committed;
- the current task remains recorded as active;
- local dirty files are preserved;
- the next Codex session resumes that task rather than selecting a new one.

See `AGENTS.md` and `.codex/AUTO_EXECUTION.md`.
