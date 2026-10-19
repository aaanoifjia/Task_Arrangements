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
M3-CONTINUE-007 ├──────── M3-INTEGRATE-008A
M3-SCHED-005 ───┘

M3-INTEGRATE-008A ─────── M3-TEST-008
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

---

## M1-CTRL-003 — Resume + Interrupt Probe

### Goal

验证 persisted thread resume 和 interrupt。

### Dependencies

`PREP-000`

### Owned Files

```text
spikes/codex_execution_probe/resume_interrupt_probe.py
spikes/codex_execution_probe/results/resume_interrupt.json
spikes/codex_execution_probe/workspaces/control/*
```

### Resume Part

1. 新建 thread。
2. 第一 turn：

```text
Remember this exact marker for this thread:
CODEX_FLOW_RESUME_MARKER_7F31
Reply only with ACK.
```

3. 保存 thread id。
4. 关闭第一个 `AsyncCodex` context。
5. 新建第二个 `AsyncCodex` context。
6. 调用：

```python
thread_resume(thread_id)
```

7. 第二 turn：

```text
Reply with only the exact marker I told you to remember earlier.
```

8. final response 必须包含：

```text
CODEX_FLOW_RESUME_MARKER_7F31
```

### Interrupt Part

独立创建一个新 thread。

使用：

```python
turn = await thread.turn(
    "Count from 1 to 100000, one integer per line. Do not summarize."
)
await turn.interrupt()
```

然后持续消费 `turn.stream()` 直到 `turn/completed`。

记录实际 terminal status。

### Acceptance

JSON：

```text
resume_verified = true
interrupt_event_received = true
interrupt_terminal_status = <actual status>
```

并确保 interrupt 后不是通过 sleep 猜测完成。

---

## M1-DESKTOP-004 — Desktop Interop Probe

### Goal

验证外部 thread 在当前 Windows Codex Desktop 中的实际可见性和 deep link 行为。

### Dependencies

`M1-RUN-002`

### Owned Files

```text
spikes/codex_execution_probe/desktop_interop_probe.ps1
spikes/codex_execution_probe/results/desktop_interop_checklist.md
```

### Implementation

1. 从 `basic_execution.json` 读取 `thread_id`。
2. 生成：

```text
codex://threads/<thread_id>
```

3. PowerShell 使用：

```powershell
Start-Process "<deep-link>"
```

4. 自动生成 checklist：

```text
- [ ] Codex Desktop opened
- [ ] Correct thread opened
- [ ] Thread appears in sidebar without restart
- [ ] Thread is searchable
- [ ] Thread is associated with expected project
```

5. 将 thread ID、测试日期、deep link 写入 checklist。
6. 不修改任何 Codex Desktop DB / LevelDB / config。

### Acceptance

脚本成功生成 checklist 并发起 deep link。

Sidebar 等 UI 观察结果由用户反馈，不让 Codex 猜测。

---

## M1-PACK-005 — Frozen Backend Feasibility Probe

### Goal

提前验证未来 Python sidecar 打包不会被 `openai-codex-cli-bin` runtime 路径机制完全阻塞。

### Dependencies

```text
M1-AUTH-001
M1-RUN-002
M1-CTRL-003
```

### Owned Files

```text
spikes/codex_execution_probe/package_probe.py
spikes/codex_execution_probe/package_probe.spec
spikes/codex_execution_probe/results/package_probe.json
```

### Implementation

`package_probe.py` 只做：

```text
print SDK version
instantiate Codex
read account
close
```

不得运行付费 / 长 turn。

使用 PyInstaller：

```powershell
.\.venv\Scripts\pyinstaller.exe --clean --noconfirm `
  --name codex-flow-package-probe `
  --collect-all openai_codex `
  --collect-all codex_cli_bin `
  spikes\codex_execution_probe\package_probe.py
```

如果 `--collect-all codex_cli_bin` 对实际 module name 不可用：

- 不自行搜索其他框架；
- 记录真实 error；
- 在 `.spec` 中显式加入安装环境中的 `codex_cli_bin` package data，再重跑一次。

只允许 PyInstaller 这一条路线。

### Acceptance

目标结果：

```text
dist/codex-flow-package-probe/codex-flow-package-probe.exe
```

可启动并输出：

```text
sdk_version
account_access_ok=true
```

若失败，保留日志并让 `M1-REPORT-006` 将 Packaging 标记为风险；不能因此更换核心架构。

---

## M1-REPORT-006 — Compatibility Gate Report

### Goal

把 M1 结果统一成后续 M2 可依赖的兼容性事实。

### Dependencies

全部：

```text
M1-AUTH-001
M1-RUN-002
M1-CTRL-003
M1-DESKTOP-004
M1-PACK-005
```

### Owned Files

```text
docs/codex-compatibility-report.md
```

### Required Table

```text
Python version
openai-codex version
Runtime version if exposed
Windows version
Account access
Thread start
Turn start
Event stream
Terminal event
Workspace write
Resume
Interrupt
Deep link launch
Desktop sidebar behavior
PyInstaller probe
```

每项只允许：

```text
PASS
FAIL
USER-CHECK
```

### Gate

以下必须 PASS 才能进入真实 SDK Adapter：

```text
Account access
Thread start
Turn start
Terminal event
Workspace write
Resume
Interrupt
```

Desktop sidebar 和 PyInstaller 不是 M2 hard gate。

---

# 7. M2 — Codex Adapter

---

## M2-INTERFACE-001 — Internal Adapter Contract

### Goal

定义 Scheduler 未来唯一可见的 Codex 接口。

### Dependencies

```text
M0-ARCH-001
M0-DOMAIN-002
M0-STATE-003
M1-REPORT-006
```

### Owned Files

```text
backend/src/codex_flow/codex_adapter/__init__.py
backend/src/codex_flow/codex_adapter/models.py
backend/src/codex_flow/codex_adapter/interface.py
```

### Required Internal Models

至少：

```text
CodexThreadRef
CodexTurnRef
CodexEvent
CodexTurnOutcome
CodexThreadSnapshot
CodexExecutionConfig
```

### EventType

固定内部 enum：

```text
THREAD_CREATED
TURN_STARTED
AGENT_MESSAGE
TOOL_STARTED
TOOL_COMPLETED
TURN_COMPLETED
TURN_FAILED
TURN_INTERRUPTED
ATTENTION_REQUIRED
TRANSPORT_ERROR
```

### Interface

使用 `Protocol` 或 ABC，全部 async：

```python
async def create_thread(...)
async def resume_thread(...)
async def start_turn(...)
async def stream_turn(...)
async def interrupt_turn(...)
async def read_thread(...)
async def set_thread_name(...)
async def close(...)
```

Scheduler 不得 import `openai_codex`。

### Acceptance

```powershell
.\.venv\Scripts\python.exe -m mypy backend\src\codex_flow\codex_adapter
```

通过。

---

## M2-FAKE-002 — Deterministic Fake Adapter

### Dependencies

`M2-INTERFACE-001`

### Owned Files

```text
backend/src/codex_flow/codex_adapter/fake.py
backend/tests/contracts/test_fake_adapter.py
```

### Required Scenarios

Fake 通过输入 scenario 控制：

```text
SUCCESS
FAILED
INTERRUPTED
SLOW_SUCCESS
SERVER_BUSY
TRANSPORT_ERROR
NEEDS_ATTENTION
```

必须：

- 生成 deterministic thread_id / turn_id
- 不访问网络
- 不 sleep 超过测试必要时间
- 记录所有 calls 供断言
- stream 产生固定 event sequence

---

## M2-SDK-003 — Official SDK Adapter

### Dependencies

```text
M2-INTERFACE-001
M1-REPORT-006
```

### Owned Files

```text
backend/src/codex_flow/codex_adapter/sdk.py
backend/tests/live/test_sdk_adapter_smoke.py
```

### Implementation

只使用：

```text
openai_codex.AsyncCodex
openai_codex.ApprovalMode
openai_codex.Sandbox
public Thread / Turn APIs
```

内部映射：

```text
internal workspace_write -> Sandbox.workspace_write
internal read_only -> Sandbox.read_only
internal full_access -> Sandbox.full_access
```

默认 approval：

```text
ApprovalMode.auto_review
```

将 SDK Notification 转成内部 `CodexEvent`。

Terminal 状态只来自 `turn/completed`。

### Acceptance

live smoke test 使用 temp workspace，完成一次 exact file write。

---

## M2-CONTRACT-004 — Adapter Contract Suite

### Dependencies

```text
M2-FAKE-002
M2-SDK-003
```

### Owned Files

```text
backend/tests/contracts/test_adapter_contract.py
```

### Required Contract Tests

同一套行为验证：

```text
create thread returns id
start turn returns id
stream includes start
stream reaches terminal
resume works
interrupt reaches terminal
read thread returns same id
set name succeeds
close is idempotent or safely repeatable
```

SDK live 部分使用 pytest marker：

```text
live_codex
```

默认普通 test suite 不运行 live Codex。

---

# 8. M3 — Deterministic DAG Engine

---

## M3-GRAPH-001 — Graph Validation

### Dependencies

`M0-DOMAIN-002`

### Owned Files

```text
backend/src/codex_flow/domain/models.py
backend/src/codex_flow/scheduler/graph.py
backend/tests/unit/test_graph.py
```

### Implementation

Pydantic models：

```text
WorkflowDefinition
TaskDefinition
Edge
RetryPolicy
```

Graph validation：

- unique task ids
- all dependencies exist
- no self dependency
- no duplicate edge
- cycle detection
- deterministic topological ordering

Cycle detection 使用显式算法（Kahn 或 DFS），不得让 LLM 判断。

---

## M3-STATE-002 — State Transition Service

### Dependencies

`M0-STATE-003`

### Owned Files

```text
backend/src/codex_flow/domain/status.py
backend/src/codex_flow/scheduler/state_machine.py
backend/tests/unit/test_state_machine.py
```

### Implementation

创建：

```text
TaskStatus
TransitionError
transition(current, target, trigger)
```

所有合法 transition 用静态表定义。

非法 transition 必须 raise。

---

## M3-READY-003 — Readiness & Failure Propagation

### Dependencies

```text
M3-GRAPH-001
M3-STATE-002
```

### Owned Files

```text
backend/src/codex_flow/scheduler/readiness.py
backend/tests/unit/test_readiness.py
```

### Rules

```text
all deps SUCCESS -> READY
no deps -> READY
any dep FAILED/INTERRUPTED/CANCELLED/SKIPPED -> BLOCKED
dep RUNNING/READY/PENDING -> BLOCKED
```

`SKIPPED` 默认不等于 SUCCESS。

---

## M3-LOCK-004 — Concurrency and Workspace Lock

### Dependencies

`M3-STATE-002`

### Owned Files

```text
backend/src/codex_flow/scheduler/locks.py
backend/tests/unit/test_locks.py
```

### Required Rules

- global semaphore
- one active turn per Codex thread
- per canonical `cwd` write lock
- read-only tasks do not take write lock
- Windows path comparison case-insensitive
- normalize path before lock key

---

## M3-SCHED-005 — Async Scheduler Core

### Dependencies

```text
M2-CONTRACT-004
M3-READY-003
M3-LOCK-004
```

### Owned Files

```text
backend/src/codex_flow/scheduler/engine.py
backend/src/codex_flow/scheduler/executor.py
backend/tests/unit/test_scheduler_core.py
```

### Implementation

Scheduler loop：

```text
recalculate readiness
↓
select READY tasks in deterministic order
↓
check global capacity
↓
check workspace lock
↓
STARTING
↓
CodexAdapter create/resume thread
↓
start turn
↓
RUNNING
↓
stream terminal
↓
SUCCESS/FAILED/INTERRUPTED
↓
recalculate readiness
```

Selection order：

```text
topological order
then task id lexical order for ties
```

禁止随机。

---

## M3-MANUAL-006 — Manual Controls

### Dependencies

`M3-SCHED-005`

### Owned Files

```text
backend/src/codex_flow/scheduler/actions.py
backend/tests/unit/test_manual_actions.py
```

### Required Actions

```text
retry
cancel
skip
mark_success
pause_workflow
resume_workflow
```

每个 action 返回明确结果，不静默失败。

---

## M3-CONTINUE-007 — Continue Existing Thread Semantics

### Dependencies

`M3-SCHED-005`

### Owned Files

```text
backend/src/codex_flow/scheduler/continuation.py
backend/tests/unit/test_continuation.py
```

### Rules

当：

```text
execution_mode = CONTINUE_THREAD
```

必须：

- `continue_from_task_id` 存在
- source TaskRun 已 SUCCESS
- source 有 thread_id
- source 当前没有 active turn
- 调用 `resume_thread(thread_id)`
- 新 TaskRun 保存同一 thread_id、新 turn_id

---

## M3-INTEGRATE-008A — Scheduler Feature Integration

### Dependencies

```text
M3-SCHED-005
M3-MANUAL-006
M3-CONTINUE-007
```

### Owned Files

```text
backend/src/codex_flow/scheduler/engine.py
backend/src/codex_flow/scheduler/actions.py
backend/src/codex_flow/scheduler/continuation.py
backend/tests/unit/test_scheduler_integration.py
```

### Goal

Integrate the scheduler core, manual controls, and continuation semantics so the
existing M3-TEST-008 scheduler matrix can exercise them without modifying
implementation files.

### Required Behavior

- `pause_workflow` prevents new READY tasks from starting; `resume_workflow`
  deterministically permits ready work to start again.
- Retry follows the existing legal retry path. After a subsequent parent
  success, readiness is recalculated and a child may become READY.
- `SKIPPED` does not release a dependent child. Explicit `mark_success` must
  recalculate readiness and may release a dependent child.
- `CONTINUE_THREAD` validates its source via `continuation.py`, resumes the
  source thread, preserves its thread id, and starts a new turn. `NEW_THREAD`
  behavior remains unchanged.
- Preserve deterministic topological selection, global capacity, workspace
  write locking, one active turn per thread, fail-closed behavior, and the
  `CodexAdapter` boundary.

Do not redesign the scheduler, add dependencies, bypass `readiness.py` or
`state_machine.py`, or change FakeCodexAdapter contracts. A real adapter
contract defect must be recorded as BLOCKED.

### Acceptance

`backend/tests/unit/test_scheduler_integration.py` covers pause/resume,
failed-parent retry followed by child release, skip blocking, mark-success
release, `CONTINUE_THREAD` resume/reused thread id, and unchanged `NEW_THREAD`.
Run the scheduler core, manual actions, continuation, readiness, locks, and
state-machine tests, plus Ruff for owned files and strict scheduler mypy.

---

## M3-TEST-008 — Scheduler Matrix

### Dependencies

```text
M3-INTEGRATE-008A
```

### Owned Files

```text
backend/tests/unit/test_scheduler_matrix.py
```

### Matrix

必须覆盖：

```text
A
A -> B
A -> B,C
B,C -> D
failure blocks children
interrupt blocks children
retry failed parent then releases child
skip does not release child
mark-success releases child
pause prevents new starts
resume releases ready task
global concurrency 1
global concurrency 2
same cwd write concurrency 1
different cwd parallel
continue thread
cycle rejected
```

全部使用 Fake Adapter。

---

# 9. M4 — Persistence & Crash Recovery

---

## M4-SCHEMA-001 — SQLite Schema & Migration 0001

### Dependencies

`M3-TEST-008`

### Owned Files

```text
backend/src/codex_flow/storage/schema.py
backend/src/codex_flow/storage/migrations/0001_initial.sql
backend/src/codex_flow/storage/migrations/__init__.py
backend/tests/integration/test_migration_0001.py
```

### Tables

固定：

```text
schema_version
workflows
tasks
edges
workflow_runs
task_runs
attempts
events
settings
```

启用：

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
```

所有 run / attempt / event 使用 immutable IDs。

---

## M4-REPO-002 — Storage Repositories

### Dependencies

`M4-SCHEMA-001`

### Owned Files

```text
backend/src/codex_flow/storage/db.py
backend/src/codex_flow/storage/repositories.py
backend/tests/integration/test_repositories.py
```

### Required Operations

CRUD 只覆盖当前阶段需要：

```text
save workflow definition
load workflow
create workflow run
create task runs
create attempt
update task run state
append event
load active runs
load attempts
```

所有 write 使用 transaction。

---

## M4-SNAPSHOT-003 — Immutable Run Snapshot

### Dependencies

`M4-REPO-002`

### Owned Files

```text
backend/src/codex_flow/storage/snapshots.py
backend/tests/integration/test_run_snapshot.py
```

### Rule

Run 开始时把：

```text
task definition
prompt
dependencies
execution config
```

全部复制到 run snapshot。

之后修改 WorkflowDefinition 不影响 active WorkflowRun。

---

## M4-ATTEMPT-004 — Transactional Attempt Start

### Dependencies

`M4-REPO-002`

### Owned Files

```text
backend/src/codex_flow/storage/attempts.py
backend/tests/integration/test_attempt_transaction.py
```

### Critical Order

必须实现：

```text
BEGIN
create Attempt
TaskRun READY -> STARTING
COMMIT
↓
then call Codex
```

获得 thread_id/turn_id 后再次 transaction 持久化。

禁止先调用 Codex 再创建 Attempt。

---

## M4-RECOVERY-005 — Startup Reconciliation

### Dependencies

```text
M4-SNAPSHOT-003
M4-ATTEMPT-004
```

### Owned Files

```text
backend/src/codex_flow/storage/recovery.py
backend/tests/integration/test_recovery.py
```

### On Startup

查询：

```text
STARTING
RUNNING
NEEDS_ATTENTION
```

对有 thread_id 的 task：

- Adapter `read_thread`
- reconcile latest turn state

对没有 thread_id 的 `STARTING`：

- 不自动重新发送 Prompt
- 标记为 recovery-required failure / explicit state
- 记录 event

原则：

```text
unknown external execution state => fail closed
```

---

## M4-DUP-006 — Duplicate Execution Protection

### Dependencies

`M4-RECOVERY-005`

### Owned Files

```text
backend/tests/integration/test_duplicate_prevention.py
```

### Required Tests

模拟 crash 点：

```text
after attempt commit before Codex call
after thread created before thread_id save
after turn started before turn_id save
while RUNNING
after terminal event before SUCCESS persisted
```

测试目标：

- 不静默重复发送 Prompt
- 未知状态不释放 downstream
- audit event 存在

---

# 10. M5 — Headless End-to-End MVP

---

## M5-CLI-001 — CLI Runner

### Dependencies

`M4-DUP-006`

### Owned Files

```text
backend/src/codex_flow/cli/__init__.py
backend/src/codex_flow/cli/main.py
backend/tests/integration/test_cli.py
```

### Commands

使用标准库 `argparse`：

```text
codex-flow run <workflow.json>
codex-flow status <run-id>
codex-flow retry <run-id> <task-id>
codex-flow cancel <run-id> <task-id>
codex-flow pause <run-id>
codex-flow resume <run-id>
```

在 `backend/pyproject.toml` 增加 console script 需要另开整合 Task 或由本任务唯一修改 pyproject。

因此本 Task **额外拥有**：

```text
backend/pyproject.toml
```

只允许新增：

```toml
[project.scripts]
codex-flow = "codex_flow.cli.main:main"
```

---

## M5-EXAMPLES-002 — Canonical Workflow Fixtures

### Dependencies

`M4-DUP-006`

### Owned Files

```text
examples/linear.json
examples/fork_join.json
examples/failure.json
examples/continue_thread.json
```

### Content

只使用已经冻结的 Workflow schema。

不创建额外功能。

---

## M5-LINEAR-003 — Real A → B End-to-End

### Dependencies

```text
M5-CLI-001
M5-EXAMPLES-002
```

### Owned Files

```text
backend/tests/live/test_e2e_linear.py
examples/e2e_workspace_linear/*
```

### Scenario

Task A：

```text
Create A.txt containing exactly A_DONE
```

Task B depends on A：

```text
Verify A.txt contains A_DONE.
Create B.txt containing exactly B_DONE
```

Assertions：

- B thread 不在 A terminal 前创建
- A.txt correct
- B.txt correct
- both SUCCESS
- distinct threads for NEW_THREAD

---

## M5-FORKJOIN-004 — Real Fork / Join + Failure

### Dependencies

`M5-LINEAR-003`

### Owned Files

```text
backend/tests/live/test_e2e_fork_join.py
backend/tests/live/test_e2e_failure.py
examples/e2e_workspace_fork_join/*
examples/e2e_workspace_failure/*
```

### Fork/Join Scenario

```text
A
├─ B
└─ C
B + C -> D
```

B/C 用不同 cwd，允许并发。

D 只能在二者 SUCCESS 后创建。

### Failure Scenario

A Prompt 明确要求运行一个必然失败的命令并停止。

验证 downstream 不创建 thread。

---

## M5-RESTART-005 — Real Restart Recovery

### Dependencies

`M5-LINEAR-003`

### Owned Files

```text
backend/tests/live/test_e2e_restart.py
examples/e2e_workspace_restart/*
```

### Scenario

通过子进程启动 runner。

Task A 进入 RUNNING 后强制 kill runner。

重新启动。

验证：

- DB run 仍存在
- recovery 执行
- 不重复发送 A Prompt
- downstream 不在未知状态下启动

---

## M5-REPORT-006 — Headless MVP Gate Report

### Dependencies

```text
M5-FORKJOIN-004
M5-RESTART-005
```

### Owned Files

```text
docs/headless-mvp-test-report.md
```

### Required Results

逐项记录：

```text
linear dependency
delayed task creation
real prompt send
terminal event
fork
join
failure blocking
retry
workspace lock
continue thread
restart recovery
duplicate prevention
```

每项：

```text
PASS / FAIL
```

全部 PASS 才进入 M6 Local API。

---

# 11. 现在应该怎么开跑

## 情况 A：Codex Flow repo 还没建

现在只发：

```text
PREP-000
```

不要同时运行其他任务。

PREP-000 完成并反馈后，立即并行 Wave 1。

---

## 情况 B：repo 已按 PREP-000 完成

现在可以同时发以下 8 个：

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

如果不想一次跑 8 个，优先级：

```text
P0:
M0-DOMAIN-002
M0-STATE-003
M1-AUTH-001
M1-RUN-002
M1-CTRL-003

P1:
M0-ARCH-001
M0-ADR-004
M0-ACCEPT-005
```

---

# 12. 每次向我反馈 Codex 结果时的格式

以后完成 Task 后，只需要提供：

```text
Task ID:
Status: SUCCESS / FAILED / BLOCKED

Files changed:
- ...

Commands/tests:
- ...
- result

Important output:
- thread_id / turn_id（如有）
- error（如有）

Codex final note:
<原样粘贴>
```

我会根据本 Dependency Graph 判断：

- 哪些 Task 已解锁
- 下一波可以并行哪些
- 是否需要补修复 Task
- 是否进入下一个 Milestone

---

# 13. 当前技术基线来源

本 Task Plan 按 2026-10-15 已确认的公开稳定能力制定：

- `openai-codex` Python SDK stable releases
- Python >= 3.10；本项目固定 3.11+
- `AsyncCodex`
- `thread_start`
- `thread_resume`
- `Thread/AsyncThread.run`
- `turn`
- `stream`
- `interrupt`
- `read`
- stable SDK pins matching Codex runtime package

固定 SDK 版本：

```text
openai-codex==0.162.1
```

后续升级 SDK 不改变本任务图；只通过 Codex Adapter contract tests 验证兼容性后升级。
