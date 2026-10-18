# Codex Flow — Agent Execution Rules

## Source of Truth

Architecture and execution planning documents are stored under:

docs/reference/

Follow those documents unless a task explicitly overrides them.

## Task Scope

When executing a task:

- Modify only files explicitly owned by that task.
- Do not expand task scope.
- Do not redesign architecture.
- Do not change dependencies unless explicitly instructed.
- Do not perform unrelated refactors.
- Do not run repository-wide autofix commands unless explicitly instructed.

If completing a task requires modifying a file outside the task's Owned Files, stop and report:

BLOCKED: requires change to <path>

## Architecture Constraints

- Scheduler control flow must be deterministic.
- Do not use an LLM to decide task dependencies or workflow progression.
- Fail closed when workflow state is ambiguous.
- CodexAdapter is the boundary for Codex integration.
- Scheduler code must not directly depend on Codex Desktop internals.
- Do not read or modify private Codex Desktop SQLite, LevelDB, renderer IPC, or other private state.
- Codex Desktop is not the authoritative workflow database.
- SQLite will be the durable local state store.
- Same-workspace concurrent write tasks must be prevented by the scheduler.

## Git Safety

Do not run:

- git commit
- git push
- git rebase
- git reset --hard

unless a task explicitly requires it.
