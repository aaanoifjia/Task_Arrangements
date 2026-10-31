# Codex Flow — Project Agent Rules

## 1. Mission

Build Codex Flow according to the frozen plans in `docs/reference/`.

Codex is an executor, not the project planner. Do not redesign the architecture, change the technology stack, infer new scope, or replace the deterministic DAG control model.

## 2. Source of Truth

Read these before making implementation decisions:

1. `.codex/progress.json` — authoritative local execution progress.
2. `.codex/AUTO_EXECUTION.md` — autonomous execution and commit protocol.
3. `docs/reference/Codex_Flow_RC_Productization_Task_Plan.md` — authoritative concrete task definitions for M11–M12.
4. `docs/reference/Codex_Flow_Late_Phase_Task_Plan.md` — authoritative concrete task definitions for M8–M10.
5. `docs/reference/Codex_Flow_Early_Phase_Task_Plan.md` — completed concrete task definitions through M7.
6. `docs/reference/Codex_Flow_Master_Roadmap.md` — milestone-level roadmap.
7. `docs/reference/codex_task_dag方案.md` — product and scheduler design rationale.
8. `docs/domain-model.md` and `docs/state-machine.md` — canonical domain/state contracts.

When two sources conflict, use this precedence:
`.codex/progress.json` for current status, then the RC/Productization Task Plan for M11–M12, then the Late Phase Task Plan for M8–M10, then the Early Phase Task Plan for M0–M7, then the Master Roadmap. Do not silently reconcile architectural conflicts; stop the affected task and record the conflict.

## 3. Autonomous Execution Mode

When the user tells you to continue the project automatically:

1. Run `git status --short` and `git log --oneline -10`.
2. Read `.codex/progress.json`.
3. If the working tree is clean and `active_task` is null, run `git pull --ff-only origin master` before selecting work, then re-read `.codex/progress.json` and the authoritative task plan.
4. If `active_task` is non-null, do not pull; resume that task only. Do not start another task.
5. If the working tree contains legitimate active-task changes, do not pull/reset/stash; resume the active task from those changes.
6. If `active_task` is null, execute `next_task`.
7. Before changing implementation files for a new task, mark that task `IN_PROGRESS` in `.codex/progress.json` and commit that progress checkpoint.
8. Push each autonomous checkpoint/block/completion commit to `origin master` immediately after the local commit succeeds.
9. Execute only the task's explicit steps and Owned Files.
10. Run the task's required tests/checks.
11. Only after acceptance passes:
   - mark the task COMPLETE in `.codex/progress.json`;
   - clear `active_task`;
   - compute/set the next deterministic task from the recorded dependency plan;
   - update `docs/current-progress.md`;
   - commit the completed task and progress update together.
12. After a task completes, immediately continue to the next deterministic dependency-ready task.
13. Do not estimate, infer, or reason about remaining quota, context, time, turn budget, execution budget, or session budget. These are host-level constraints, not project stopping conditions.
14. Never voluntarily stop because you believe such a budget may be low or nearly exhausted. If the host actually terminates execution, the checkpoint/progress mechanism handles recovery.
15. If a task requires user interaction, credentials, GUI confirmation, or a decision not encoded in the task spec, mark it BLOCKED and stop at that task.
16. If a deterministic validation reveals a bounded adjacent integration repair, apply the Bounded Automatic Remediation rules in Section 5 instead of stopping.
17. When a milestone preflight task/checklist exists, execute it before continuing implementation-heavy work in that milestone.

Never skip a failed/blocked prerequisite.

### Autonomous Stop Conditions

In autonomous mode, Codex may stop voluntarily only when one of these is true:

- the requested project target is complete;
- a genuine user/manual gate is reached;
- required credentials or external interaction are unavailable;
- an authoritative task specification is missing and the issue does not qualify for bounded automatic remediation;
- a required host/system prerequisite is missing and is not explicitly authorized for installation;
- a real blocker or architectural conflict prevents deterministic continuation.

Completion of one task, elapsed wall-clock time, long context, token usage, perceived quota pressure, or a guessed execution/session budget are not stop conditions.

If the host/runtime forcibly ends the invocation, do not attempt special cleanup. Durable progress already exists in Git and `.codex/progress.json`; the next invocation resumes from that state.

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
- Do not perform unrelated refactors.
- Do not change dependencies or package versions unless the task explicitly requires it.
- Do not run repository-wide autofix commands.

### Bounded Automatic Remediation

A non-owned-file requirement is no longer automatically a stop condition.

If a failing compiler, typecheck, test, import, route wiring check, or other deterministic acceptance check proves that the active task requires a small adjacent repair outside its Owned Files, Codex may create and execute a bounded remediation automatically.

A bounded remediation is allowed only when all of these are true:

1. the required file/path is directly identified by the failing validation or is the immediate typed/wiring dependency that caused it;
2. the repair is necessary to satisfy the already-authoritative task contract;
3. the repair does not change architecture, product scope, TaskStatus semantics, persistence authority, public behavior beyond the already-authoritative contract, or dependency graph semantics;
4. it does not add/upgrade an external package unless the parent task already explicitly requires that package;
5. it does not require credentials, GUI confirmation, privileged system changes, destructive Git operations, or user product decisions;
6. the repair is a small explicit set of files in the same subsystem, not a broad refactor.

When allowed:

- derive a remediation ID from the parent task, e.g. `<PARENT>-R1`, `<PARENT>-R2`;
- record the parent task, reason, remediation files, failing validation, and acceptance in `.codex/progress.json.remediation_history`;
- checkpoint and push the remediation before editing;
- modify only the recorded remediation files plus progress/current-progress;
- run the narrow failing validation and relevant regression;
- commit/push the remediation;
- restore/resume the parent task automatically and continue;
- do not stop merely to ask for authorization for this bounded repair.

If any criterion above is false, record a real BLOCKED state and stop.

### Milestone Preflight

Before the first implementation-heavy task of a new milestone, or when a milestone first encounters a missing host toolchain, run the milestone's authoritative preflight task/checklist if one exists.

Preflight should check declared host prerequisites early (for example Python, Node/npm, Rust/Cargo, compiler/build tools, WebView2, PyInstaller) and report all known missing prerequisites together instead of discovering them one task at a time.

Host/system installation policy:

- repository-local dependencies explicitly required by a task may be installed normally;
- system-level toolchains or runtimes are not installed silently by default;
- a system-level toolchain may be installed only when either:
  1. an authoritative task explicitly authorizes that exact installation, or
  2. the user's current invocation explicitly authorizes that exact named toolchain;
- use the official vendor installer/source and the least-privileged supported install mode;
- if elevation, license acceptance, interactive GUI, reboot, credentials, or an additional unapproved system component is required, stop and report it;
- never broaden one authorization (for example Rust) into another (for example Visual Studio Build Tools).

## 6. Git Protocol

For autonomous mode, commits are required at small-task boundaries.

Allowed:
- `git status`
- `git diff`
- `git add <explicit paths>`
- `git commit -m "..."`
- `git pull --ff-only origin master` only when the working tree is clean and no task is active
- `git push origin master` after every autonomous checkpoint, blocker, and completed-task commit

Automatic Git policy:
- pull mode: `safe_when_clean`
- push mode: enabled
- never pull while `active_task` is non-null or legitimate active-task work is dirty
- if pull is rejected because histories diverged, stop and report the conflict; do not merge/rebase automatically
- if push is rejected, stop and report the remote-state conflict; do not force-push

Do not:
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

## 10. Windows Desktop UI / E2E Automation

### Desktop architecture

Codex Flow 的生产 UI 是 Tauri + WebView2 Desktop application，不是普通浏览器网页。Desktop 验证必须针对真实 installed application；Vite dev server、独立 React、独立 backend 或未安装 release exe 只能作为诊断层，不能替代 installed Desktop acceptance。

### Validation evidence priority

按以下优先级获取确定性证据：

1. SQLite / REST API / logs / process tree / filesystem；
2. 真实 installed Tauri application + WebView2 CDP；
3. Tauri/WebDriver Desktop E2E；
4. generic Computer Use / screenshot / accessibility 作为 fallback。

只要 CDP、WebDriver、API、SQLite 或其它确定性手段可验证，就不得仅因任务涉及 GUI 而停止并要求人工确认。只有这些方式均无法自动验证时，才可标记 manual GUI gate。

### WebView2 debugging

WebView2 remote debugging 仅可在 test、smoke、diagnostics 启动时临时开启，绑定地址必须是 `127.0.0.1`；正常生产启动不得默认开放 remote debugging port。自动化应优先通过 `/json/list` 发现目标并验证其属于 Codex Flow，而非普通 Chrome/Edge 页面。

### Computer Use fallback

generic Computer Use 无法读取 WebView2 accessibility tree 或 screenshot 时，不得反复尝试同一种 Computer Use；应切换到 WebView2 CDP 或官方 Tauri/WebDriver Desktop E2E。

### Installed-build acceptance

发布 smoke 必须覆盖真实 installed NSIS payload，并验证 installed executable 与 NSIS payload identity。不得以 frontend dev server、standalone backend 或 uninstalled release exe 替代最终 Desktop smoke。

### Automation stop rule

普通 GUI 自动化失败不是 blocker。无人值守任务仅可在 UAC/管理员授权、密码/登录/验证码等新凭据、Windows reboot、修改 firewall/group/security policy、安装 driver、购买/license、destructive Git、无法自动解决的 architecture conflict 或用户明确产品决策时停止。其它失败应自动收集证据、修复、重建、安装并继续。
