# Codex Flow — Project Agent Rules

## 1. Mission

Build Codex Flow according to the frozen plans in `docs/reference/`.

Codex is an executor, not the project planner. Do not redesign the architecture, change the technology stack, infer new scope, or replace the deterministic DAG control model.

## 2. Source of Truth

Read these before making implementation decisions:

1. `.codex/progress.json` — authoritative local execution progress.
2. `.codex/AUTO_EXECUTION.md` — autonomous execution and commit protocol.
3. `docs/reference/Codex_Flow_Early_Phase_Task_Plan.md` — concrete task definitions and dependencies through M5.
4. `docs/reference/Codex_Flow_Master_Roadmap.md` — milestone-level roadmap.
5. `docs/reference/codex_task_dag方案.md` — product and scheduler design rationale.
6. `docs/domain-model.md` and `docs/state-machine.md` — canonical domain/state contracts.

When two sources conflict, use this precedence:
`.codex/progress.json` for current status, then the concrete Early Phase Task Plan, then the Master Roadmap. Do not silently reconcile architectural conflicts; stop the affected task and record the conflict.

## 3. Autonomous Execution Mode

When the user tells you to continue the project automatically:

1. Read `.codex/progress.json`.
2. Run `git status --short`.
3. If `active_task` is non-null, resume that task only. Do not start another task.
4. If `active_task` is null, execute `next_task`.
5. Before changing implementation files for a new task, mark that task `IN_PROGRESS` in `.codex/progress.json` and commit that progress checkpoint.
6. Execute only the task's explicit steps and Owned Files.
7. Run the task's required tests/checks.
8. Only after acceptance passes:
   - mark the task COMPLETE in `.codex/progress.json`;
   - clear `active_task`;
   - compute/set the next deterministic task from the recorded dependency plan;
   - update `docs/current-progress.md`;
   - commit the completed task and progress update together.
9. Continue to the next task while quota/time remains.
10. If a task requires user interaction, credentials, GUI confirmation, or a decision not encoded in the task spec, mark it BLOCKED and stop at that task.

Never skip a failed/blocked prerequisite.

## 4. Resume After Interruption

An interrupted session must be recoverable without guessing.

At startup:

- If the working tree is dirty and `active_task` is set, assume those changes belong to that active task unless files clearly fall outside its Owned Files.
- Do not reset, stash, discard, or overwrite dirty work.
- Re-run the active task's validation/tests, inspect remaining steps, and continue.
- Completed earlier tasks must already exist as commits and must not be reimplemented.

If the working tree is clean and `active_task` is set, continue from the task spec and progress notes.

## 5. Task Scope

For every task:

- Modify only its Owned Files plus `.codex/progress.json` and `docs/current-progress.md`.
- Do not expand scope.
- Do not perform unrelated refactors.
- Do not change dependencies or package versions unless the task explicitly requires it.
- Do not run repository-wide autofix commands.
- If the task requires a non-owned file change, stop and record:
  `BLOCKED: requires change to <path>`

## 6. Git Protocol

For autonomous mode, commits are required at small-task boundaries.

Allowed:
- `git status`
- `git diff`
- `git add <explicit paths>`
- `git commit -m "..."`
- `git pull --ff-only` only when the working tree is clean and no task is active

Do not:
- `git push` unless the user explicitly asks
- `git rebase`
- `git reset --hard`
- `git clean -fd`
- automatic stash
- amend a completed task commit unless explicitly requested

Commit conventions:

- Start checkpoint: `chore(progress): start <TASK_ID>`
- Completed task: `task(<TASK_ID>): complete <short title>`
- Blocker metadata only: `chore(progress): block <TASK_ID>`

A task is not COMPLETE until its acceptance checks pass.

## 7. Architecture Constraints

- Scheduler control flow is deterministic.
- LLMs never decide task dependencies, workflow progression, retry eligibility, or failure propagation.
- Fail closed when workflow state is ambiguous.
- Codex integration is behind `CodexAdapter`.
- Scheduler code must not depend on Codex Desktop internals.
- Do not read or modify private Codex Desktop SQLite, LevelDB, renderer IPC, or private state.
- Codex Desktop is not authoritative workflow state.
- SQLite is the durable local state store.
- Same-workspace concurrent write tasks must be serialized.
- WorkflowDefinition != WorkflowRun.
- TaskRun != Attempt.
- Retry creates a new Attempt.

## 8. Dynamic Progress Rule

Do not hard-code a current task or blocker in this file.

The authoritative current execution state is always:

`.codex/progress.json`

Use `active_task`, `next_task`, `completed_tasks`, and `blocked_tasks` from that file. Historical blockers that have already been resolved must not stop later tasks.

## 9. Test Discipline

Use the project virtual environment:

`\.venv\Scripts\python.exe`

For pure core work, run targeted pytest, Ruff, and mypy checks specified by the task. Before completing a core milestone task, also run the relevant existing unit suite to catch regressions.

Never treat assistant text, elapsed time, or file existence alone as Codex turn completion. Real execution completion must come from the Codex terminal event.
