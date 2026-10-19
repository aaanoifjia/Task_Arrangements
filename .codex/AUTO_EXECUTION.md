# Codex Flow — Autonomous Execution Protocol

This file defines how a Codex invocation advances the project across many small tasks while preserving durable recovery if the host/runtime forcibly interrupts execution.

## Core Principle

One small task is the unit of durable progress.

Every task follows:

```text
checkpoint active task
→ implement only that task
→ validate
→ update progress
→ commit completed task
→ continue
```

If the host/runtime forcibly ends execution during implementation, all earlier successful tasks are already committed and `.codex/progress.json` records which task is active.

Codex must not predict or estimate quota, context, time, turn budget, execution budget, or session budget. Those are host-level constraints. As long as the invocation is still running and no genuine blocker exists, continue executing the next deterministic task.

## Session Startup

Execute in this order:

```powershell
git status --short
git log --oneline -10
```

Then read:

1. `AGENTS.md`
2. `.codex/progress.json`
3. the active/next task spec
4. relevant canonical docs

### Dirty working tree

If dirty and `active_task` is non-null:
- do not pull;
- do not reset/stash;
- verify changed paths belong to the active task;
- resume the active task.

If dirty and `active_task` is null:
- stop and report the unexpected dirty files instead of guessing ownership.

### Clean working tree

If clean and `active_task` is null:
- execute `next_task`.

A clean tree may use `git pull --ff-only` before starting only if the user has configured a remote and no task is active.

## Starting a Task

Before implementation:

1. Confirm all dependencies in `.codex/progress.json` are COMPLETE.
2. Set:
   - `active_task.id`
   - `active_task.status = "IN_PROGRESS"`
   - `active_task.started_at`
   - `active_task.note`
3. Set `next_task = null`.
4. Commit only the progress checkpoint:

```text
chore(progress): start <TASK_ID>
```

This checkpoint makes any externally forced interruption recoverable. It is not a reason to stop voluntarily.

## Executing a Task

Follow the task spec literally.

Rules:
- no research unless the task explicitly requests research;
- no alternative architecture;
- no dependency upgrades;
- no unrelated cleanup;
- no files outside Owned Files;
- no repository-wide format/fix command.

If an implementation choice is not defined but multiple choices are equivalent and local to the Owned Files, choose the smallest standard-library/simple implementation consistent with canonical docs.

If the choice changes architecture or public contracts, block instead of deciding.

## Completing a Task

A task can become COMPLETE only when all explicit acceptance checks pass.

Then:

1. Update `.codex/progress.json`:
   - add task to `completed_tasks`;
   - remove it from `blocked_tasks` if present;
   - clear `active_task`;
   - set `next_task` to the next dependency-ready task;
   - record validation summary.
2. Update `docs/current-progress.md`.
3. Stage only:
   - task Owned Files;
   - `.codex/progress.json`;
   - `docs/current-progress.md`.
4. Commit:

```text
task(<TASK_ID>): complete <short title>
```

5. Immediately continue with the next deterministic dependency-ready task.

Do not stop to report a successfully completed individual task. Do not decide that "resources", "budget", "time", "context", or "quota" may be running low. Continue until a genuine stop condition occurs or the host/runtime actually terminates the invocation.

## Blocking a Task

Block rather than guess when:

- an explicit prerequisite is not COMPLETE;
- user login/approval/manual GUI check is required;
- canonical docs conflict;
- an external dependency fails in a way not covered by the task;
- completing the task requires modifying non-owned files;
- required credentials or environment state are unavailable.

Update progress with:
- task ID;
- exact blocker;
- last successful validation;
- deterministic next action.

Commit blocker metadata only if no unsafe/failed implementation files need to be included:

```text
chore(progress): block <TASK_ID>
```

Then stop autonomous progression unless another independent task is explicitly marked READY in progress.

## Failure vs Interruption

`BLOCKED`: known external prerequisite or manual input prevents work.

`FAILED`: implementation or acceptance checks failed and the task requires repair.

`IN_PROGRESS`: execution was externally interrupted before task completion, or the host/runtime forcibly terminated the invocation.

Codex must not set or preserve `IN_PROGRESS` merely because it predicts that quota, context, time, or an execution/session budget may be low.

An abrupt externally forced end requires no special cleanup. The next invocation resumes the active task.

## Host-Level Budget Rule

Budget handling is not part of project planning.

Codex must never voluntarily stop because it estimates or suspects any of the following:

- remaining quota;
- remaining tokens/context;
- elapsed or remaining wall-clock time;
- turn budget;
- execution budget;
- session budget;
- "enough work for this turn";
- likelihood that the host may stop soon.

There is no project-defined numeric execution budget.

If the host/runtime has not actually terminated the invocation, continue. The durable checkpoint/commit protocol exists specifically so an actual external termination is safe.

A message such as "execution budget ended", "turn budget is exhausted", or similar must not be used as a self-selected stop reason unless the host/runtime has in fact already forced termination.

## Task Selection

`.codex/progress.json.next_task` is authoritative.

Do not scan the roadmap and choose a more interesting task.

Only when a task completes should `next_task` be advanced according to the dependency graph already encoded in the plans/progress file.

## User-Interaction Gates

Do not wait indefinitely for manual actions.

If a task needs a user check, set it BLOCKED with `requires_user = true` and stop.

Current known manual gate later in M1:
- Desktop deep-link/sidebar observation in `M1-DESKTOP-004`.

## Push Policy

Local commits are required for durability.
Automatic push is disabled.

Only push when the user explicitly asks for remote synchronization.
