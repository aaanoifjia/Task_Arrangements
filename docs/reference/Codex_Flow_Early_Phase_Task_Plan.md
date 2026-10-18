# Codex Flow — Early Phase Executable Task Plan

> 版本：v1.0  
> 日期：2026-10-15  
> 作用：从项目第 0 步开始，到 Headless End-to-End MVP（M5）为止的**具体任务级路线图**。  
> 上位文档：`Codex_Flow_Master_Roadmap.md`、`codex_task_dag方案.md`  
> 原则：Codex 只执行明确步骤，不负责调研、架构判断、技术选型或重新规划。

---

# 1. 固定执行规则

后续把本文件中的 Task 交给 Codex 时，统一遵守以下规则。

## 1.1 Codex 的职责

Codex 只负责：

- 创建 / 修改指定文件
- 按指定接口实现代码
- 执行指定测试命令
- 输出测试结果
- 报告阻塞项

Codex 不负责：

- 搜索替代技术方案
- 重新设计架构
- 更换技术栈
- 扩大 Scope
- 自动新增未要求功能
- “顺便优化”其他模块
- 修改上位 Roadmap

---

## 1.2 并行安全规则

多个 Codex Task 可以并行运行，但必须满足：

1. 每个 Task 有明确 `Owned Files`。
2. Task 不得修改非 Owned Files。
3. 不执行全仓库 `ruff --fix .`、自动 formatter 或批量重写。
4. 只对自己拥有的文件运行格式化 / lint。
5. 不执行 `git commit`、`git rebase`、`git reset --hard`。
6. 不删除其他 Task 新建的文件。
7. 如果发现必须修改非 Owned File 才能完成任务：
   - 不修改；
   - 输出 `BLOCKED: requires change to <path>`。
8. Live Codex Probe 使用各自独立临时 workspace，不能修改 Codex Flow repo 本身的业务文件。

---

## 1.3 Python 基线

固定：

```text
Python: 3.11+
Codex Python SDK: openai-codex==0.162.1
Internal models: Pydantic v2
Async runtime: asyncio
Database: sqlite3 standard library
Tests: pytest
Lint: ruff
Type check: mypy
```

Codex SDK 使用公开稳定接口：

```text
AsyncCodex
thread_start
thread_resume
AsyncThread.turn
AsyncTurnHandle.stream
AsyncTurnHandle.interrupt
AsyncThread.read
```

不使用 SDK 私有模块。

---

## 1.4 Headless Core 的固定目录结构

早期阶段最终形成：

```text
codex-flow/
│
├── README.md
├── AGENTS.md
├── .gitignore
├── .editorconfig
│
├── docs/
│   ├── reference/
│   ├── adr/
│   ├── architecture.md
│   ├── domain-model.md
│   ├── state-machine.md
│   └── v1-acceptance.md
│
├── backend/
│   ├── pyproject.toml
│   ├── src/
│   │   └── codex_flow/
│   │       ├── __init__.py
│   │       ├── domain/
│   │       ├── codex_adapter/
│   │       ├── scheduler/
│   │       ├── storage/
│   │       └── cli/
│   └── tests/
│       ├── unit/
│       ├── contracts/
│       ├── integration/
│       └── live/
│
├── spikes/
│   └── codex_execution_probe/
│
└── examples/
```

---

# 2. Dependency Graph

```text
PREP-000
│
├─────────────── M0-ARCH-001
├─────────────── M0-DOMAIN-002
├─────────────── M0-STATE-003
├─────────────── M0-ADR-004
├─────────────── M0-ACCEPT-005
│
├─────────────── M1-AUTH-001
├─────────────── M1-RUN-002
└─────────────── M1-CTRL-003

M1-RUN-002 ───── M1-DESKTOP-004
M1-AUTH-001 ─┐
M1-RUN-002 ──┼── M1-PACK-005
M1-CTRL-003 ─┘

M1-AUTH-001 ─┐
M1-RUN-002 ──┤
M1-CTRL-003 ─┼── M1-REPORT-006
M1-DESKTOP-004┤
M1-PACK-005 ──┘

M0-DOMAIN-002 ─────────── M3-GRAPH-001
M0-STATE-003 ──────────── M3-STATE-002

M0-ARCH-001 ─┐
M0-DOMAIN-002│
M0-STATE-003 ├── M2-INTERFACE-001
M1-REPORT-006┘

M2-INTERFACE-001 ──────── M2-FAKE-002
M2-INTERFACE-001 ──────── M2-SDK-003

M2-FAKE-002 ─┐
M2-SDK-003 ──┴─────────── M2-CONTRACT-004

M3-GRAPH-001 ─┐
M3-STATE-002 ─┴────────── M3-READY-003

M3-STATE-002 ──────────── M3-LOCK-004

M2-CONTRACT-004 ─┐
M3-READY-003 ────┼─────── M3-SCHED-005
M3-LOCK-004 ─────┘

M3-SCHED-005 ──────────── M3-MANUAL-006
M3-SCHED-005 ──────────── M3-CONTINUE-007

M3-MANUAL-006 ─┐
M3-CONTINUE-007 ├──────── M3-TEST-008
M3-SCHED-005 ───┘

M3-TEST-008 ───────────── M4-SCHEMA-001
M4-SCHEMA-001 ─────────── M4-REPO-002
M4-REPO-002 ───────────── M4-SNAPSHOT-003
M4-REPO-002 ───────────── M4-ATTEMPT-004

M4-SNAPSHOT-003 ─┐
M4-ATTEMPT-004 ──┴─────── M4-RECOVERY-005
M4-RECOVERY-005 ───────── M4-DUP-006

M4-DUP-006 ────────────── M5-CLI-001
M4-DUP-006 ────────────── M5-EXAMPLES-002

M5-CLI-001 ───────┐
M5-EXAMPLES-002 ──┴────── M5-LINEAR-003

M5-LINEAR-003 ─────────── M5-FORKJOIN-004
M5-LINEAR-003 ─────────── M5-RESTART-005

M5-FORKJOIN-004 ─┐
M5-RESTART-005 ──┴─────── M5-REPORT-006
```

---

# 3. Parallel Waves

## Wave 0 — 唯一前置

```text
PREP-000
```

如果 repo 还不存在，先只运行这一项。

---

## Wave 1 — PREP-000 完成后立即全部可并行

以下 8 个 Task 的 Owned Files 不重叠，可以同时启动：

```text
M0-ARCH-001
M0-DOMAIN-002
M0-STATE-003
M0-ADR-004
M0-ACCEPT-005

M1-AUTH-001
M1-RUN-002
M1-CTRL-003
```

---

## Wave 2

当对应依赖完成后可以并行：

```text
M1-DESKTOP-004
M1-PACK-005

M3-GRAPH-001
M3-STATE-002
```

`M1-REPORT-006` 等 M1 五项全部完成后启动。

---

## Wave 3

```text
M2-INTERFACE-001
```

同时，如果 M3 前置已经完成：

```text
M3-READY-003
M3-LOCK-004
```

---

## Wave 4

`M2-INTERFACE-001` 完成后：

```text
M2-FAKE-002
M2-SDK-003
```

两者可以并行。

---

## Wave 5+

按 Dependency Graph 继续执行。

---

# 4. PREP-000 — Repository Bootstrap

## Goal

创建 Codex Flow monorepo 的最小、稳定骨架，使后续文档、SDK Probe 和业务模块可以并行开发。

## Dependencies

无。

## Owned Files

```text
README.md
AGENTS.md
.gitignore
.editorconfig
backend/pyproject.toml
backend/src/codex_flow/__init__.py
backend/tests/.gitkeep
frontend/.gitkeep
desktop/.gitkeep
docs/reference/*
spikes/.gitkeep
examples/.gitkeep
```

## Execution Steps

1. 如果当前目录不是 Git repository，执行：

```powershell
git init
```

如果已经是 Git repository，不重新初始化。

2. 创建目录：

```text
backend/src/codex_flow
backend/tests
frontend
desktop
docs/reference
spikes
examples
```

3. 如果 repo 根目录已有：

```text
Codex_Flow_Master_Roadmap.md
codex_task_dag方案.md
```

将它们移动到：

```text
docs/reference/
```

如果不存在，不生成虚假的替代内容。

4. 创建 `backend/pyproject.toml`：

固定：

```toml
[build-system]
requires = ["hatchling>=1.27,<2"]
build-backend = "hatchling.build"

[project]
name = "codex-flow-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "openai-codex==0.162.1",
  "pydantic>=2.12,<3",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.4,<10",
  "pytest-asyncio>=1.2,<2",
  "ruff>=0.14,<1",
  "mypy>=1.18,<2",
  "pyinstaller>=6.16,<7",
]

[tool.hatch.build.targets.wheel]
packages = ["src/codex_flow"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.mypy]
python_version = "3.11"
strict = true
packages = ["codex_flow"]
```

5. `backend/src/codex_flow/__init__.py`：

```python
__version__ = "0.1.0"
```

6. `.gitignore` 至少覆盖：

```text
.venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
dist/
build/
*.egg-info/
*.db
*.sqlite
*.sqlite3
*.log
.env
```

7. `AGENTS.md` 写入项目执行原则：

- Follow files in `docs/reference/` as architecture source.
- Do not change architecture or dependencies unless task explicitly says so.
- Modify only files owned by the assigned task.
- Do not use private Codex Desktop DB/state.
- Do not add LLM decisions to scheduler control flow.
- Fail closed on ambiguous workflow state.

8. `README.md` 只写：

- Project name
- one-paragraph goal
- current phase: early headless core
- backend setup commands

9. 从 repo 根目录执行：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e "backend[dev]"
.\.venv\Scripts\python.exe -c "import codex_flow; print(codex_flow.__version__)"
```

10. 不实现任何 Scheduler / Adapter / UI。

## Deliverables

上述 Owned Files。

## Acceptance Criteria

最后一条 Python 命令输出：

```text
0.1.0
```

并且：

```powershell
git status --short
```

只显示本 Task 创建的文件。

---

# 5. M0 — Architecture Freeze Tasks

---

## M0-ARCH-001 — Architecture Contract

### Goal

创建 `docs/architecture.md`，把长期架构层级固定下来。

### Dependencies

`PREP-000`

### Owned Files

```text
docs/architecture.md
```

### Required Content

必须明确：

```text
UI
↓
Local API
↓
Application Services
↓
Scheduler
↓
CodexAdapter
↓
OpenAI Codex SDK/App Server
```

以及：

```text
SQLite
```

是 authoritative durable local state。

必须写入：

- Python backend
- FastAPI later
- React + React Flow later
- Tauri + Python sidecar later
- CodexAdapter boundary
- Scheduler never calls SDK directly
- Desktop UI is not authoritative state
- no browser/Desktop RPA in core
- no master-agent scheduling
- deterministic fail-closed DAG
- async execution from backend core
- same-workspace write lock

### Explicit Non-Goals

写入：

- no multi-user cloud
- no automatic dependency inference
- no prompt rewriting
- no private Codex Desktop DB
- no LangGraph control plane

### Acceptance

运行：

```powershell
Select-String -Path docs\architecture.md -Pattern "CodexAdapter","SQLite","fail-closed","workspace"
```

四项均有匹配。

---

## M0-DOMAIN-002 — Domain Model Specification

### Goal

创建 canonical domain model 文档。

### Dependencies

`PREP-000`

### Owned Files

```text
docs/domain-model.md
```

### Required Entities

必须定义：

```text
WorkflowDefinition
TaskDefinition
Edge
WorkflowRun
TaskRun
Attempt
Event
```

### TaskDefinition Fields

至少：

```text
id
name
prompt
cwd
dependencies
execution_mode
continue_from_task_id
model
reasoning_effort
sandbox
approval_mode
timeout_seconds
retry_policy
```

### TaskRun Fields

至少：

```text
id
workflow_run_id
task_definition_id
status
thread_id
turn_id
active_attempt_id
started_at
completed_at
last_error
```

### Attempt

每次 retry 新建 Attempt，不覆盖旧记录。

### ExecutionMode

固定：

```text
NEW_THREAD
CONTINUE_THREAD
```

### Acceptance

文档必须明确写出：

```text
Definition != Run
TaskRun != Attempt
```

以及 Workflow Run 使用 immutable snapshot。

---

## M0-STATE-003 — State Machine Specification

### Goal

冻结 Task Run 状态机。

### Dependencies

`PREP-000`

### Owned Files

```text
docs/state-machine.md
```

### Canonical Status

固定：

```text
PENDING
BLOCKED
READY
STARTING
RUNNING
NEEDS_ATTENTION
SUCCESS
FAILED
INTERRUPTED
SKIPPED
CANCELLED
```

### Required Rules

写出完整 transition table。

至少：

```text
PENDING -> READY
PENDING -> BLOCKED

READY -> STARTING
STARTING -> RUNNING
STARTING -> FAILED

RUNNING -> SUCCESS
RUNNING -> FAILED
RUNNING -> INTERRUPTED
RUNNING -> NEEDS_ATTENTION
RUNNING -> CANCELLED

NEEDS_ATTENTION -> RUNNING
NEEDS_ATTENTION -> FAILED
NEEDS_ATTENTION -> CANCELLED
```

Manual override 的 `SKIPPED` / `SUCCESS` 必须标记 audit event。

Terminal states 至少：

```text
SUCCESS
FAILED
INTERRUPTED
SKIPPED
CANCELLED
```

### Acceptance

文档必须明确：

```text
all dependencies SUCCESS -> READY
any required dependency non-SUCCESS terminal -> downstream remains BLOCKED
```

---

## M0-ADR-004 — Architecture Decision Records

### Goal

创建固定 ADR。

### Dependencies

`PREP-000`

### Owned Files

```text
docs/adr/ADR-001-python-backend.md
docs/adr/ADR-002-codex-adapter.md
docs/adr/ADR-003-sqlite.md
docs/adr/ADR-004-fastapi.md
docs/adr/ADR-005-react-flow.md
docs/adr/ADR-006-tauri-sidecar.md
docs/adr/ADR-007-deterministic-dag.md
docs/adr/ADR-008-workspace-lock.md
```

### Format

每个 ADR 固定四段：

```text
Status
Context
Decision
Consequences
```

`Status` 全部为：

```text
Accepted
```

不新增其他 ADR。

---

## M0-ACCEPT-005 — V1 Acceptance Contract

### Goal

把 V1 Definition of Done 写成机器/人工可逐项检查的 checklist。

### Dependencies

`PREP-000`

### Owned Files

```text
docs/v1-acceptance.md
```

### Required Checklist

必须包含 Master Roadmap 中 22 条 V1 Definition of Done，并额外为每条加：

```text
Verification:
```

Verification 只能是：

- automated test
- manual UX check
- both

不得改变原始 V1 Scope。

---

# 6. M1 — Codex Execution Spike

所有 M1 Live Probe 必须使用独立目录：

```text
spikes/codex_execution_probe/workspaces/<probe-name>/
```

不能把 Codex 的写操作指向 Codex Flow repo。

---

## M1-AUTH-001 — SDK / Authentication Probe

### Goal

验证固定 SDK 版本、bundled runtime 和现有 Codex 登录可用。

### Dependencies

`PREP-000`

### Owned Files

```text
spikes/codex_execution_probe/auth_probe.py
spikes/codex_execution_probe/results/auth_probe.json
```

### Implementation

脚本必须：

1. import：

```python
import openai_codex
from openai_codex import Codex
```

2. 记录：

```text
python_version
openai_codex_version
platform
```

3. 使用：

```python
with Codex() as codex:
    account = codex.account(refresh_token=False)
```

4. 将 `account.model_dump(mode="json")` 递归清洗：

key 名包含以下字符串时，value 替换成 `"***REDACTED***"`：

```text
token
secret
key
credential
```

5. 写入 JSON。

6. 不主动触发 browser login。
7. 如果没有现有登录，退出非 0 并输出：

```text
NO_EXISTING_CODEX_SESSION
```

### Run

```powershell
.\.venv\Scripts\python.exe spikes\codex_execution_probe\auth_probe.py
```

### Acceptance

- exit code 0
- result JSON 存在
- SDK version 是 `0.162.1`
- 不包含 token / secret 字段原值

---

## M1-RUN-002 — Real Thread + Turn + Stream Probe

### Goal

证明程序可以创建新 Codex Thread、发送完整 Prompt、观察事件，并实际写文件。

### Dependencies

`PREP-000`

### Owned Files

```text
spikes/codex_execution_probe/basic_execution_probe.py
spikes/codex_execution_probe/results/basic_execution.json
spikes/codex_execution_probe/workspaces/basic/*
```

### Implementation

使用：

```python
AsyncCodex
Sandbox.workspace_write
```

创建独立 workspace。

程序预先创建：

```text
INPUT.txt
```

内容固定：

```text
CODEX_FLOW_PROBE_INPUT
```

Prompt 固定要求 Codex：

```text
Read INPUT.txt.
Create OUTPUT.txt containing exactly:
CODEX_FLOW_PROBE_OUTPUT
Do not modify or create any other file.
```

执行：

```python
thread = await codex.thread_start(
    cwd=str(workspace),
    sandbox=Sandbox.workspace_write,
)
await thread.set_name("Codex Flow Probe - Basic")
turn = await thread.turn(prompt)
```

遍历：

```python
async for event in turn.stream():
```

记录：

```text
thread_id
turn_id
event.method list
turn/completed status
```

成功后：

- `OUTPUT.txt` 必须存在
- 内容必须严格等于 `CODEX_FLOW_PROBE_OUTPUT`

JSON 记录：

```text
thread_id
turn_id
completed_status
saw_turn_started
saw_turn_completed
output_verified
```

### Acceptance

全部为真：

```text
saw_turn_started
saw_turn_completed
output_verified
```

且 terminal status 为 completed/success 对应 SDK 实际稳定值。

禁止通过 assistant 文本推断成功。