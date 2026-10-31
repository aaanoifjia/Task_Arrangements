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

Then read `.codex/progress.json`.

If the working tree is clean and `active_task` is null:

```powershell
git pull --ff-only origin master
```

After a successful pull, re-read:

1. `AGENTS.md`
2. `.codex/progress.json`
3. the active/next task spec
4. relevant canonical docs

If `active_task` is non-null, or legitimate active-task work is dirty, do not pull. Resume that task from the current local state.

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
- automatically run `git pull --ff-only origin master`;
- re-read progress/task definitions after the pull;
- execute `next_task`.

If the fast-forward pull cannot be completed safely, stop and report the repository conflict. Never merge, rebase, reset, or stash automatically.

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

After the checkpoint commit succeeds, automatically run:

```powershell
git push origin master
```

If the push is rejected, stop and report the remote conflict. Never force-push.

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

## Bounded Automatic Remediation

Do not turn every adjacent integration defect into a user-facing blocker.

When the active task's deterministic validation fails because a small, directly implicated non-owned file must be repaired, first evaluate the Bounded Automatic Remediation criteria in `AGENTS.md`.

If it qualifies:

1. keep the parent task logically IN_PROGRESS;
2. create a deterministic remediation ID `<PARENT>-R<n>`;
3. append a remediation record to `.codex/progress.json.remediation_history` containing:
   - remediation ID;
   - parent task;
   - reason;
   - exact remediation files;
   - failing validation;
   - intended acceptance;
   - status;
4. checkpoint:
   `chore(progress): start <REMEDIATION_ID>`
5. push the checkpoint;
6. edit only the remediation files plus progress/current-progress;
7. run the failing validation and the smallest relevant regression;
8. mark the remediation COMPLETE in `remediation_history`;
9. commit:
   `task(<REMEDIATION_ID>): complete bounded remediation`
10. push;
11. resume the parent task automatically;
12. re-run the parent acceptance and continue.

Do not edit the authoritative roadmap just to represent a bounded remediation; the durable remediation record in progress is sufficient.

A bounded remediation must become a real blocker if it requires:
- architecture or product-scope decisions;
- a new/unapproved external dependency;
- credentials, login, GUI confirmation, elevation, reboot, or destructive Git;
- a broad refactor or unrelated cleanup;
- a system-level toolchain that is not explicitly authorized.

## Milestone Preflight

When an authoritative milestone preflight task/checklist exists, execute it before implementation-heavy milestone work.

If a missing host prerequisite is found mid-milestone, prefer one bounded preflight/remediation that checks the complete declared toolchain set instead of repeatedly failing task-by-task.

System-level installation rules:
- default: detect and report, do not install;
- install only an exact named toolchain explicitly authorized by the authoritative task or the user's current invocation;
- use official vendor sources and least-privileged supported mode;
- never infer authorization for adjacent components;
- if installation requires elevation, interactive acceptance, reboot, credentials, or another unapproved system component, BLOCK.

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

5. Push the completed-task commit:

```powershell
git push origin master
```

6. Immediately continue with the next deterministic dependency-ready task.

Do not stop to report a successfully completed individual task. Do not decide that "resources", "budget", "time", "context", or "quota" may be running low. Continue until a genuine stop condition occurs or the host/runtime actually terminates the invocation.

## Blocking a Task

Block rather than guess when:

- an explicit prerequisite is not COMPLETE;
- user login/approval/manual GUI check is required;
- canonical docs conflict;
- an external dependency fails in a way not covered by the task;
- completing the task requires a non-owned-file change that does not qualify for bounded automatic remediation;
- required credentials or environment state are unavailable;
- a required system-level prerequisite is missing and its exact installation is not explicitly authorized.

Update progress with:
- task ID;
- exact blocker;
- last successful validation;
- deterministic next action.

## Windows Desktop UI / E2E Automation

Codex Flow 的生产 UI 是 Tauri + WebView2。真实 Desktop 验证优先使用确定性证据：SQLite/REST/logs/process tree/filesystem，其次是 installed Tauri + WebView2 CDP，再其次是 Tauri/WebDriver；generic Computer Use、screenshot 和 accessibility 仅作 fallback。能够通过 CDP、API、SQLite 或日志验证时，不得把普通 GUI 操作当作 manual gate。

发布 smoke 必须运行真实 installed NSIS payload；frontend dev server、standalone React/backend 和未安装 release exe 不能替代 installed acceptance。WebView2 remote debugging 只能在 test/smoke/diagnostics 临时开启，且只绑定 `127.0.0.1`，不得写入正常生产默认配置。自动化必须通过 `/json/list` 验证 target 属于 Codex Flow Desktop。

Computer Use 无法读取 WebView2 accessibility tree 或 screenshot 时，切换到 WebView2 CDP 或 Tauri/WebDriver，不得循环重复同一失败方式。普通 GUI 自动化失败不是 blocker；只有 UAC/管理员授权、新凭据/验证码、reboot、安全策略修改、driver/license、destructive Git、无法自动解决的架构冲突或明确产品决策才停止。其余失败应收集证据、修复、重建、安装并继续。

Commit blocker metadata only if no unsafe/failed implementation files need to be included:

```text
chore(progress): block <TASK_ID>
```

After a blocker metadata commit succeeds, automatically push it to `origin master`.

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

## Git Synchronization Policy

Local commits are required for durability.

Automatic pull:

- mode is `safe_when_clean`;
- at invocation startup, pull with `git pull --ff-only origin master` only when the working tree is clean and `active_task` is null;
- after pulling, re-read `.codex/progress.json` and authoritative task definitions;
- never pull across legitimate active-task dirty work;
- never auto-merge or auto-rebase a divergence.

Automatic push:

- enabled for autonomous execution;
- push every successful checkpoint, blocker, and completed-task commit with `git push origin master`;
- never force-push;
- on rejection, stop and report the conflict instead of rewriting history.

Forbidden synchronization shortcuts remain:

- automatic stash;
- `git reset --hard`;
- `git clean -fd`;
- `git rebase`;
- force push.
