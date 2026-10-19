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

M5-LINEAR-003 ─────────── M5-FAILMAP-004A
M5-FAILMAP-004A ───────── M5-FORKJOIN-004
M5-LINEAR-003 ─────────── M5-RUNNER-005A
M5-RUNNER-005A ────────── M5-RESTART-005

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

## M5-FAILMAP-004A — Tool Failure Propagation

### Dependencies

```text
M5-LINEAR-003
M3-CONTINUE-007
```

### Owned Files

```text
backend/src/codex_flow/codex_adapter/sdk.py
backend/src/codex_flow/scheduler/executor.py
backend/src/codex_flow/scheduler/continuation.py
backend/tests/unit/test_tool_failure_mapping.py
backend/tests/unit/test_continuation.py
```

### Goal

A Codex turn must not be classified as Task SUCCESS merely because the SDK emits
`TURN_COMPLETED` when a command/tool execution inside that turn failed.

### Required Behavior

- For `item/completed` command-execution notifications, preserve stable
  `item_type`, optional `item_id`, `status`, `exit_code`, and optional `command`
  in `CodexEvent.details`, while continuing to emit `EventType.TOOL_COMPLETED`.
- A command completion is failed when its status is `failed` or `declined`, or
  when a present exit code is non-zero. Contradictory explicit command outcome
  data fails closed.
- `TaskExecutor` and `ThreadContinuation` must keep consuming until the real
  terminal event. `TURN_COMPLETED` is SUCCESS only when no failed command was
  observed; otherwise it is FAILED. `TURN_FAILED`, `TURN_INTERRUPTED`,
  `ATTENTION_REQUIRED`, and `TRANSPORT_ERROR` retain their canonical mappings.
- `CONTINUE_THREAD` validates and resumes the source thread while retaining the
  source thread id and storing the new turn id. `NEW_THREAD` remains unchanged.
- Preserve deterministic selection, concurrency and workspace/thread locks,
  fail-closed behavior, and the `CodexAdapter` boundary. Do not change the
  `EventType` enum or public `CodexAdapter` interface.

### Acceptance

- Unit tests cover successful and failed/declined command completions,
  terminal-event consumption after a failed command, child blocking after a
  parent command failure, and the same behavior for `CONTINUE_THREAD`.
- Existing scheduler core, manual actions, continuation, readiness, lock, and
  state-machine tests pass.
- Ruff passes for the owned files and strict mypy passes for scheduler code.

---

## M5-FORKJOIN-004 — Real Fork / Join + Failure

### Dependencies

```text
M5-LINEAR-003
M5-FAILMAP-004A
```

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

## M5-RUNNER-005A — Durable Headless Runner Integration

### Dependencies

```text
M4-DUP-006
M5-CLI-001
M5-LINEAR-003
```

### Owned Files

```text
backend/src/codex_flow/runtime/__init__.py
backend/src/codex_flow/runtime/runner.py
backend/src/codex_flow/cli/main.py
backend/src/codex_flow/storage/repositories.py
backend/src/codex_flow/codex_adapter/sdk.py
backend/src/codex_flow/scheduler/executor.py
backend/tests/integration/test_persistent_runner.py
backend/tests/integration/test_cli.py
backend/tests/live/test_sdk_restart_read.py
```

### Goal

Provide the minimum production headless runner that connects the frozen
deterministic scheduler semantics to durable SQLite execution and startup recovery.

### Required Behavior

- `codex-flow run <workflow.json> [--db <path>]` opens/migrates SQLite, validates
  and persists the frozen workflow, creates an immutable workflow-run snapshot and
  task runs, then starts only dependency-ready tasks in deterministic order. The
  default database is `.codex-flow.sqlite3` in the current directory.
- A NEW_THREAD external start uses `AttemptStarter` so the persisted READY →
  STARTING Attempt transaction completes before thread creation and turn start.
  RUNNING is persisted only after a real `TURN_STARTED` event.
- Consume each terminal stream using the existing executor failure mapping;
  persist its canonical status and recalculate readiness using the existing rules.
  Failed, interrupted, skipped, and ambiguous recovery states cannot release a
  dependent task.
- On an existing unfinished run, do not create another run, resend an already
  started prompt, or create another Attempt. Reconcile with `StartupReconciler`
  before any new execution, and fail closed if more than one active matching run
  exists.
- A fresh `SdkCodexAdapter` must read a persisted thread id through the supported
  resume/read path, cache it, and never create a new turn or resend a prompt.
- Keep SQLite behind repositories, retain all writes as transactions, and only
  wire the existing CLI `run` command. Do not introduce a second DAG algorithm or
  change the SDK version, adapter interface, EventType, or scheduler semantics.

### Acceptance

- Offline integration coverage proves fresh durable creation, immutable snapshots,
  transactional attempts, STARTED/RUNNING/terminal persistence, dependency
  progression, fail-closed failure behavior, and no duplicate run/attempt/prompt
  across restart reconciliation.
- A live fresh-adapter SDK check proves a persisted thread id can be read without
  creating a turn.
- Existing M4 repository, snapshot, attempt, recovery, and duplicate-prevention
  tests; scheduler unit suite; CLI integration tests; Ruff on owned files; and
  strict mypy on affected packages all pass.

---

## M5-RESTART-005 — Real Restart Recovery

### Dependencies

```text
M5-LINEAR-003
M5-RUNNER-005A
```

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


# 11. M6 — Local API & Runtime Service

## M6 Goal

Expose the completed M5 durable headless runtime through a local FastAPI service without moving workflow authority out of SQLite or bypassing the deterministic scheduler/runtime rules.

Frozen architecture for this milestone:

~~~text
UI / future desktop
        ↓
FastAPI Local Service
        ↓
Application Services
        ↓
Durable Runtime / Scheduler
        ↓
SQLite + CodexAdapter
~~~

Rules for all M6 tasks:

- SQLite remains authoritative durable state.
- API code must not import or expose OpenAI Codex SDK-specific objects.
- API routes must not implement DAG scheduling logic.
- API routes must not infer dependencies, rewrite prompts, or decide task progression.
- DurableRunner / scheduler semantics remain deterministic and fail closed.
- All external execution remains behind CodexAdapter.
- No multi-user auth, cloud deployment, browser/Desktop RPA, or master-LLM control plane.
- M6 is local-only. Bind-address/auth hardening belongs to later milestones.
- Tests use FakeCodexAdapter unless a task explicitly requires a live Codex check.
- Existing M0–M5 regression tests must continue to pass.

## M6 Deterministic Task Order

~~~text
M6-API-001
↓
M6-CONFIG-002
↓
M6-SCHEMA-003
↓
M6-STORE-004
↓
M6-WF-SVC-005
↓
M6-WF-API-006
↓
M6-RUNTIME-007
↓
M6-RUN-SVC-008
↓
M6-RUN-API-009
↓
M6-EVENT-SVC-010
↓
M6-WS-011
↓
M6-LIFECYCLE-012
↓
M6-SYSTEM-013
↓
M6-INTEGRATE-014
↓
M6-GATE-015
↓
M6-REPORT-016
~~~

The order above is the deterministic autonomous execution order even when a later task would otherwise be dependency-ready.

---

## M6-API-001 — FastAPI Bootstrap

### Dependencies

M5-REPORT-006

### Owned Files

~~~text
backend/pyproject.toml
backend/src/codex_flow/api/__init__.py
backend/src/codex_flow/api/app.py
backend/tests/api/test_app_bootstrap.py
~~~

### Implementation

Add the local-service dependencies required by the frozen architecture:

~~~text
fastapi
uvicorn
~~~

Add httpx to dev dependencies for API tests.

Use bounded compatible version ranges; do not upgrade or change existing Codex/Pydantic pins.

Create:

~~~python
create_app(...) -> FastAPI
~~~

Requirements:

- importing the API package performs no DB, network, Codex, or filesystem side effects;
- app construction is explicit through create_app;
- OpenAPI generation succeeds;
- no SDK-specific type appears in route/API modules;
- no production server is started during import.

### Acceptance

- API bootstrap test passes.
- Existing backend import tests pass.
- Ruff passes for owned Python files.
- strict mypy passes for the API package.

---

## M6-CONFIG-002 — Local Service Configuration & DB Lifespan Foundation

### Dependencies

M6-API-001

### Owned Files

~~~text
backend/src/codex_flow/api/config.py
backend/src/codex_flow/api/lifespan.py
backend/src/codex_flow/api/app.py
backend/tests/api/test_service_config.py
~~~

### Implementation

Define deterministic local service configuration without adding a settings framework dependency.

At minimum:

~~~text
db_path
event_poll_interval_seconds
~~~

Default DB path:

~~~text
.codex-flow.sqlite3
~~~

relative to the process current working directory.

create_app must allow an explicit DB path override for tests and future desktop startup.

Lifespan foundation:

- open/migrate the SQLite DB on app startup;
- expose repository/connection through typed application state helpers;
- close the DB on shutdown;
- never open a second authoritative DB implicitly;
- no Codex call during this task.

### Acceptance

- explicit temp DB path is honored;
- default path resolution is deterministic;
- migration runs once through existing storage code;
- app shutdown closes the connection;
- no global module-level connection exists.

---

## M6-SCHEMA-003 — Public API DTO & Error Contract

### Dependencies

M6-CONFIG-002

### Owned Files

~~~text
backend/src/codex_flow/api/schemas.py
backend/src/codex_flow/api/errors.py
backend/tests/api/test_api_schemas.py
~~~

### Implementation

Define SDK-independent Pydantic API models for at least:

~~~text
ErrorResponse
WorkflowSummary
WorkflowDetail
RunStartResponse
RunSummary
RunDetail
TaskRunView
AttemptView
EventView
~~~

Rules:

- IDs and statuses serialize as stable strings.
- WorkflowDetail may embed the frozen WorkflowDefinition representation.
- API DTOs must not contain sqlite3.Row or openai_codex SDK objects.
- Error shape is deterministic:

~~~json
{
  "error": {
    "code": "STABLE_CODE",
    "message": "human readable message"
  }
}
~~~

Provide helpers for 404, 409, and invalid-request errors.

### Acceptance

- schema round-trip/serialization tests pass;
- OpenAPI can generate every public DTO;
- SDK types are absent from API schema modules.

---

## M6-STORE-004 — API Query Repository Extensions

### Dependencies

M6-SCHEMA-003

### Owned Files

~~~text
backend/src/codex_flow/storage/repositories.py
backend/tests/integration/test_api_repository_queries.py
~~~

### Implementation

Add only query operations required by M6:

~~~text
list_workflows
get_workflow_run
list_workflow_runs
load_task_runs
get_task_run
load_attempts
load_events_for_run
load_events_after
~~~

Requirements:

- preserve all existing M4/M5 write behavior;
- deterministic ordering for every list;
- event ordering must use created_at then id as a stable tie-break;
- filters use IDs, never raw SQL supplied by callers;
- no ORM or new DB dependency;
- no schema migration unless a hard requirement is discovered; if migration is truly required, BLOCK instead of silently altering M4 schema.

### Acceptance

- empty/list/single/missing query cases pass;
- event cursor ordering is deterministic;
- M4 repository and migration suites remain green.

---

## M6-WF-SVC-005 — Workflow Application Service

### Dependencies

M6-STORE-004

### Owned Files

~~~text
backend/src/codex_flow/application/__init__.py
backend/src/codex_flow/application/workflows.py
backend/tests/unit/test_workflow_service.py
~~~

### Implementation

Create an application-service layer between routes and repositories.

Support:

~~~text
save workflow
update workflow
list workflows
get workflow
~~~

Rules:

- validate input through WorkflowDefinition;
- save the editable WorkflowDefinition only;
- never mutate an existing WorkflowRun snapshot;
- application service owns validation/error translation;
- route code must not execute SQL.

### Acceptance

- create/update/list/get tests pass;
- editing a workflow does not mutate an existing run snapshot;
- malformed DAG/domain input is rejected before persistence.

---

## M6-WF-API-006 — Workflow REST API

### Dependencies

M6-WF-SVC-005

### Owned Files

~~~text
backend/src/codex_flow/api/routes/__init__.py
backend/src/codex_flow/api/routes/workflows.py
backend/src/codex_flow/api/app.py
backend/tests/api/test_workflow_routes.py
~~~

### Endpoints

~~~text
POST /api/workflows
PUT  /api/workflows/{workflow_id}
GET  /api/workflows
GET  /api/workflows/{workflow_id}
~~~

Rules:

- POST returns 201.
- PUT requires path/body workflow IDs to match.
- GET missing workflow returns stable 404 error contract.
- routes call WorkflowApplicationService only;
- no scheduler/Codex calls from workflow routes;
- response bodies use M6 API schemas.

### Acceptance

- create → get → update → list integration passes against temp SQLite DB;
- OpenAPI contains the four routes;
- no route accesses private repository connection state.

---

## M6-RUNTIME-007 — Async Runtime Manager & Non-blocking Start

### Dependencies

~~~text
M5-RUNNER-005A
M6-STORE-004
~~~

### Owned Files

~~~text
backend/src/codex_flow/runtime/runner.py
backend/src/codex_flow/runtime/manager.py
backend/src/codex_flow/runtime/__init__.py
backend/tests/integration/test_runtime_manager.py
backend/tests/integration/test_persistent_runner.py
~~~

### Implementation

Refactor DurableRunner only as needed to support a non-blocking local service while preserving CLI behavior.

Provide a RuntimeManager that:

- prepares/persists a new WorkflowRun before external execution;
- returns run_id without waiting for the full workflow to finish;
- executes the persisted run in a tracked asyncio background task;
- tracks active local background tasks by run_id;
- prevents a second active run for the same workflow;
- exposes wait(run_id) for deterministic tests;
- removes finished local tasks from its in-memory registry;
- never treats the in-memory registry as authoritative durable state.

DurableRunner must preserve:

~~~text
snapshot before execution
Attempt before Codex call
RUNNING only after TURN_STARTED
terminal event before terminal TaskRun state
fail-closed recovery
no duplicate prompt on restart
~~~

The existing CLI synchronous run behavior must remain compatible.

### Acceptance

- start returns a persisted run_id before Fake adapter workflow completion is awaited;
- duplicate active start is rejected deterministically;
- wait(run_id) observes final durable state;
- existing persistent-runner/restart tests pass.

---

## M6-RUN-SVC-008 — Run & Task Query Application Service

### Dependencies

M6-RUNTIME-007

### Owned Files

~~~text
backend/src/codex_flow/application/runs.py
backend/tests/unit/test_run_service.py
~~~

### Implementation

Support:

~~~text
start workflow run
list runs
get run
list task runs
get task run
list attempts for task run
~~~

Start semantics:

- load persisted WorkflowDefinition by ID;
- reject missing workflow;
- reject a second active run for the same workflow with conflict;
- delegate execution only to RuntimeManager;
- return run_id immediately.

Read semantics:

- map repository rows to public DTO-compatible data;
- no SDK objects;
- no direct SQL.

### Acceptance

- missing workflow -> not found;
- active duplicate -> conflict;
- start returns run ID before completion;
- task/attempt history remains available after completion.

---

## M6-RUN-API-009 — Run & Task REST API

### Dependencies

~~~text
M6-WF-API-006
M6-RUN-SVC-008
~~~

### Owned Files

~~~text
backend/src/codex_flow/api/routes/runs.py
backend/src/codex_flow/api/app.py
backend/tests/api/test_run_routes.py
~~~

### Endpoints

~~~text
POST /api/workflows/{workflow_id}/runs
GET  /api/runs
GET  /api/runs/{run_id}
GET  /api/runs/{run_id}/tasks
GET  /api/runs/{run_id}/tasks/{task_id}
GET  /api/runs/{run_id}/tasks/{task_id}/attempts
~~~

POST start returns HTTP 202 with run_id.

Requirements:

- starting a run must not block until Codex/Fake completion;
- all reads come from SQLite;
- history remains readable after app/runtime task completion;
- missing resource and active-run conflict use the stable error envelope.

### Acceptance

- API start returns before background Fake workflow finishes;
- polling run endpoint reaches terminal state;
- task and attempt endpoints reflect durable state;
- app restart against the same DB retains history.

---

## M6-EVENT-SVC-010 — Durable Event & Task-State Stream Service

### Dependencies

M6-RUN-API-009

### Owned Files

~~~text
backend/src/codex_flow/application/events.py
backend/src/codex_flow/application/event_stream.py
backend/tests/unit/test_event_service.py
backend/tests/integration/test_event_stream.py
~~~

### Implementation

Build read-only streaming primitives over durable state.

Requirements:

- durable events come from SQLite, never an in-memory-only event bus;
- support a stable after-event cursor;
- deterministic order is created_at then id;
- stream service can observe TaskRun state changes by polling durable task rows;
- emit a task snapshot only when the durable snapshot changes;
- emit Codex/runtime events without duplication;
- polling interval is injectable for tests;
- disconnected consumers do not affect workflow execution.

Internal stream message kinds:

~~~text
snapshot
event
~~~

No new persistent schema is required.

### Acceptance

- reconnect with cursor does not replay acknowledged events;
- two events with equal timestamps retain deterministic ID ordering;
- task status snapshot changes are observed;
- stream consumer cancellation does not cancel runtime work.

---

## M6-WS-011 — WebSocket Run Stream

### Dependencies

M6-EVENT-SVC-010

### Owned Files

~~~text
backend/src/codex_flow/api/routes/ws.py
backend/src/codex_flow/api/app.py
backend/tests/api/test_run_websocket.py
~~~

### Endpoint

~~~text
WS /ws/runs/{run_id}
~~~

Optional query:

~~~text
after=<event_id>
~~~

Behavior:

- reject/close missing run deterministically;
- send initial durable task snapshot;
- send subsequent snapshot messages only when task state changes;
- send persisted event messages in stable order;
- reconnect after event ID resumes without duplicating acknowledged events;
- client disconnect never changes scheduler/runtime state.

No SDK event object may cross the WebSocket boundary; only internal API DTO payloads are sent.

### Acceptance

- Fake workflow produces observable START/RUNNING/terminal progression and persisted events;
- reconnect cursor test passes;
- two simultaneous WebSocket clients do not alter execution.

---

## M6-LIFECYCLE-012 — FastAPI Runtime Lifespan & Startup Recovery

### Dependencies

~~~text
M6-RUNTIME-007
M6-WS-011
~~~

### Owned Files

~~~text
backend/src/codex_flow/api/lifespan.py
backend/src/codex_flow/api/app.py
backend/src/codex_flow/runtime/manager.py
backend/tests/api/test_app_lifecycle.py
~~~

### Implementation

Wire the local service lifecycle:

Startup order:

~~~text
open/migrate DB
↓
construct repository
↓
construct CodexAdapter
↓
run StartupReconciler
↓
construct RuntimeManager/application services
↓
accept requests
~~~

Requirements:

- startup recovery occurs before any API run start can execute;
- recovery must not resend an ambiguous existing Prompt;
- recovered runs/tasks remain queryable through API;
- app state contains only the current process service objects;
- SQLite remains authoritative;
- shutdown stops accepting new work and closes resources deterministically;
- shutdown must not mark unfinished external work SUCCESS;
- if local background execution is interrupted by shutdown, durable state must remain recoverable on next startup.

For tests, create_app must support an injected adapter or adapter factory so API tests never use live Codex.

### Acceptance

- startup recovery ordering is proven;
- same DB reopened by a new app instance retains run history;
- recovered ambiguous task remains non-releasing;
- adapter close and DB close occur exactly once.

---

## M6-SYSTEM-013 — Health & Local Runtime Status API

### Dependencies

M6-LIFECYCLE-012

### Owned Files

~~~text
backend/src/codex_flow/api/routes/system.py
backend/src/codex_flow/api/app.py
backend/tests/api/test_system_routes.py
~~~

### Endpoints

~~~text
GET /healthz
GET /api/system/status
~~~

/healthz:

- lightweight local process health;
- no Codex network call.

/api/system/status returns SDK-independent local status only:

~~~text
service status
DB reachable
schema version
active local runtime count
~~~

Must not expose:

- tokens;
- credentials;
- private Codex config;
- Desktop DB/config state.

### Acceptance

- health works with an empty migrated DB;
- status reflects active Fake runtime count;
- no secrets are present in serialized output.

---

## M6-INTEGRATE-014 — Local API End-to-End Integration

### Dependencies

~~~text
M6-WF-API-006
M6-RUN-API-009
M6-WS-011
M6-SYSTEM-013
~~~

### Owned Files

~~~text
backend/src/codex_flow/api/app.py
backend/src/codex_flow/api/lifespan.py
backend/src/codex_flow/api/routes/workflows.py
backend/src/codex_flow/api/routes/runs.py
backend/src/codex_flow/api/routes/ws.py
backend/src/codex_flow/application/workflows.py
backend/src/codex_flow/application/runs.py
backend/src/codex_flow/application/events.py
backend/src/codex_flow/application/event_stream.py
backend/src/codex_flow/runtime/manager.py
backend/src/codex_flow/runtime/runner.py
backend/src/codex_flow/storage/repositories.py
backend/tests/api/test_api_integration.py
~~~

### Integration Scenario

Using temp SQLite + FakeCodexAdapter:

~~~text
start app
↓
save A -> B workflow through REST
↓
GET workflow confirms persistence
↓
POST run returns 202 + run_id without waiting for completion
↓
WebSocket observes durable state/event progression
↓
poll run/task/attempt endpoints
↓
run reaches SUCCESS
↓
restart FastAPI app with same DB
↓
workflow + run + tasks + attempts + events still queryable
~~~

Also execute a failed-parent workflow and verify:

~~~text
parent FAILED
child BLOCKED
no downstream external execution
API reflects durable states
~~~

This task may make bounded repairs inside its Owned Files to satisfy the already-defined M6 contracts. It must not change architecture, public domain states, SDK version, or M0–M5 semantics.

### Acceptance

- complete integration scenario passes;
- M4/M5 persistence and restart suites remain green;
- no API route imports openai_codex;
- Ruff and strict mypy pass for affected packages.

---

## M6-GATE-015 — Local API Acceptance Matrix

### Dependencies

M6-INTEGRATE-014

### Owned Files

~~~text
backend/src/codex_flow/api/**
backend/src/codex_flow/application/**
backend/src/codex_flow/runtime/manager.py
backend/src/codex_flow/runtime/runner.py
backend/src/codex_flow/storage/repositories.py
backend/tests/api/test_local_api_matrix.py
~~~

### Required Matrix

All use temp SQLite and FakeCodexAdapter unless otherwise stated:

~~~text
app boot / shutdown
DB migration / reopen
workflow create
workflow update
workflow list / get
invalid workflow rejected
run start is non-blocking
second active run conflict
run list / get
task list / get
attempt history
successful dependency release
failed parent blocks child
history survives app restart
startup recovery runs before new execution
recovered ambiguous task does not release child
event order deterministic
event cursor reconnect
WebSocket initial snapshot
WebSocket live state change
WebSocket durable event delivery
multiple WebSocket clients
health endpoint
system status
no SDK objects in API contract
no direct Codex SDK import from API/application layers
M5 headless regression suite
~~~

This is a gate-and-repair task: bounded implementation repairs are allowed only within the Owned Files above when required by an existing M6 contract.

Do not weaken assertions to obtain PASS.

### Acceptance

- complete matrix passes;
- relevant M0–M5 regression suites pass;
- Ruff passes;
- strict mypy passes;
- no live Codex usage is required for this gate.

---

## M6-REPORT-016 — Local API Milestone Gate Report

### Dependencies

M6-GATE-015

### Owned Files

~~~text
docs/local-api-test-report.md
~~~

### Required Results

Record each as PASS / FAIL with concrete evidence:

~~~text
FastAPI bootstrap
deterministic local DB configuration
workflow save/update/list/get
non-blocking run start
run/task/attempt history
durable state after app restart
startup recovery before new starts
no duplicate active workflow run
failed dependency blocking through API
event ordering
event cursor reconnect
WebSocket task status stream
WebSocket persisted Codex/runtime events
health/status endpoints
SQLite remains authoritative
CodexAdapter boundary preserved
no master LLM control
M5 regression
~~~

All must PASS before M7 Visual DAG UI begins.

On PASS:

- mark M6-REPORT-016 COMPLETE;
- set next_task = null unless an authoritative M7 concrete task plan already exists;
- update docs/current-progress.md to state M6 complete / M7 awaiting concrete task definitions.

---

# 12. M7 — Visual DAG UI

## M7 Goal

Build the first usable local visual client over the completed M6 API. M7 is React + TypeScript + React Flow only; SQLite and the backend remain authoritative.

This plan intentionally targets roughly five times the implementation workload of M6. Tasks remain small enough for durable checkpoints, but the milestone includes a complete frontend from an empty directory through an integrated DAG editor and live run monitor.

### Frozen boundaries

- React + TypeScript + Vite.
- React Flow package: `@xyflow/react`.
- Local M6 REST/WebSocket API is the only runtime/backend interface.
- UI never calls Codex SDK directly.
- UI never decides scheduler progression, retry eligibility or failure propagation.
- No prompt rewriting or automatic dependency inference.
- No private Codex Desktop DB/config access.
- No Tauri/Desktop packaging in M7.
- No durable manual Retry/Pause/Resume runtime controls in M7; those are M8 human-in-the-loop/reliability work.
- Open-in-Codex is implemented as the documented `codex://threads/<thread_id>` URI contract; full manual Desktop UX verification is deferred to the desktop/manual gate.
- Prefer plain CSS and React primitives. Do not add a design-system framework.
- Frontend tests must not consume live Codex.

## M7 Deterministic Task Order

```text
M7-FE-001
↓
M7-FE-002
↓
M7-FE-003
↓
M7-FE-004
↓
M7-FE-005
↓
M7-FE-006
↓
M7-FE-007
↓
M7-FE-008
↓
M7-WF-009
↓
M7-WF-010
↓
M7-WF-011
↓
M7-EDIT-012
↓
M7-EDIT-013
↓
M7-EDIT-014
↓
M7-EDIT-015
↓
M7-EDIT-016
↓
M7-EDIT-017
↓
M7-EDIT-018
↓
M7-EDIT-019
↓
M7-EDIT-020
↓
M7-EDIT-021
↓
M7-EDIT-022
↓
M7-EDIT-023
↓
M7-EDIT-024
↓
M7-EDIT-025
↓
M7-EDIT-026
↓
M7-EDIT-027
↓
M7-EDIT-028
↓
M7-EDIT-029
↓
M7-EDIT-030
↓
M7-EDIT-031
↓
M7-EDIT-032
↓
M7-EDIT-033
↓
M7-EDIT-034
↓
M7-EDIT-035
↓
M7-EDIT-036
↓
M7-EDIT-037
↓
M7-RUN-038
↓
M7-RUN-039
↓
M7-RUN-040
↓
M7-RUN-041
↓
M7-RUN-042
↓
M7-RUN-043
↓
M7-RUN-044
↓
M7-RUN-045
↓
M7-RUN-046
↓
M7-RUN-047
↓
M7-RUN-048
↓
M7-RUN-049
↓
M7-RUN-050
↓
M7-RUN-051
↓
M7-RUN-052
↓
M7-RUN-053
↓
M7-NAV-054
↓
M7-UX-055
↓
M7-INTEGRATE-056
↓
M7-GATE-057
↓
M7-REPORT-058
```

Execute in exactly this order even when later tasks could technically be dependency-ready.

---

## M7-FE-001 — Frontend React/Vite Bootstrap

### Dependencies

```text
M6-REPORT-016
```

### Owned Files

```text
frontend/package.json
frontend/package-lock.json
frontend/index.html
frontend/vite.config.ts
frontend/src/main.tsx
frontend/src/App.tsx
```

### Implementation

- Initialize React + TypeScript + Vite. Add react, react-dom, @xyflow/react, react-router-dom. Add dev dependencies for TypeScript, Vite, Vitest, jsdom, Testing Library, user-event, ESLint and React/TS plugins. Scripts: dev, build, test, test:run, typecheck, lint. No Tailwind/design-system dependency.

### Acceptance

- npm install succeeds; npm run build succeeds; app mounts without backend dependency.

---

## M7-FE-002 — Strict TypeScript, Test & Lint Baseline

### Dependencies

```text
M7-FE-001
```

### Owned Files

```text
frontend/tsconfig.json
frontend/tsconfig.app.json
frontend/tsconfig.node.json
frontend/eslint.config.js
frontend/src/test/setup.ts
frontend/src/App.test.tsx
```

### Implementation

- Enable strict TypeScript and deterministic Vitest/jsdom setup. Configure ESLint for React hooks and TypeScript. Keep generated/build artifacts out of source.

### Acceptance

- typecheck, lint and first Vitest test pass.

---

## M7-FE-003 — Visual Tokens & Global CSS Foundation

### Dependencies

```text
M7-FE-002
```

### Owned Files

```text
frontend/src/styles/tokens.css
frontend/src/styles/global.css
frontend/src/main.tsx
```

### Implementation

- Create plain CSS variables for spacing, typography, borders, surfaces, statuses and focus states. Desktop-first neutral UI. No hard-coded task-status logic in CSS beyond presentation tokens.

### Acceptance

- App renders with global styles; no inline global style duplication.

---

## M7-FE-004 — Application Router & Shell

### Dependencies

```text
M7-FE-003
```

### Owned Files

```text
frontend/src/app/router.tsx
frontend/src/app/AppShell.tsx
frontend/src/app/AppShell.css
frontend/src/App.tsx
frontend/src/main.tsx
```

### Implementation

- Create routes for /, /workflows/:workflowId, /runs, /runs/:runId. Add persistent navigation and content shell. Unknown route shows local Not Found view.

### Acceptance

- Router navigation tests pass and direct route rendering works.

---

## M7-FE-005 — Public API Type Models

### Dependencies

```text
M7-FE-004
```

### Owned Files

```text
frontend/src/api/types.ts
frontend/src/api/types.test.ts
```

### Implementation

- Mirror only the public M6 REST/WebSocket contract: WorkflowDefinition, TaskDefinition, Edge, RunSummary/Detail, TaskRunView, AttemptView, EventView, error envelope and stream messages. Do not import backend or SDK code.

### Acceptance

- Representative payloads typecheck; status/execution/sandbox values are constrained string unions.

---

## M7-FE-006 — HTTP API Client Foundation

### Dependencies

```text
M7-FE-005
```

### Owned Files

```text
frontend/src/api/http.ts
frontend/src/api/client.ts
frontend/src/api/client.test.ts
```

### Implementation

- Create typed fetch wrapper using relative /api paths. Parse stable error envelope into ApiError. Support AbortSignal. No hidden retries and no business-state inference.

### Acceptance

- Success, 404, 409, 500 and malformed response tests pass.

---

## M7-FE-007 — WebSocket Client Foundation

### Dependencies

```text
M7-FE-006
```

### Owned Files

```text
frontend/src/api/ws.ts
frontend/src/api/ws.test.ts
```

### Implementation

- Create SDK-independent run WebSocket client for /ws/runs/{runId}?after=. Expose message/close/error hooks and explicit close. Do not mutate workflow state inside transport code.

### Acceptance

- URL/cursor/message parsing/close tests pass with fake WebSocket.

---

## M7-FE-008 — Frontend Test Fixtures & Network Mocks

### Dependencies

```text
M7-FE-007
```

### Owned Files

```text
frontend/src/test/fixtures.ts
frontend/src/test/mockFetch.ts
frontend/src/test/mockWebSocket.ts
```

### Implementation

- Add deterministic workflow/run/task/attempt/event fixtures and lightweight fetch/WebSocket mocks used by later UI tests. No production dependency on test code.

### Acceptance

- Fixtures conform to API types and mocks support ordered assertions.

---

## M7-WF-009 — Workflow API Resource Layer

### Dependencies

```text
M7-FE-008
```

### Owned Files

```text
frontend/src/features/workflows/api.ts
frontend/src/features/workflows/api.test.ts
```

### Implementation

- Implement list/get/create/update calls over ApiClient. Keep transport separate from React components.

### Acceptance

- All four M6 workflow endpoints mapped and tested.

---

## M7-WF-010 — Workflow List Page

### Dependencies

```text
M7-WF-009
```

### Owned Files

```text
frontend/src/features/workflows/WorkflowListPage.tsx
frontend/src/features/workflows/WorkflowListPage.css
frontend/src/app/router.tsx
frontend/src/features/workflows/WorkflowListPage.test.tsx
```

### Implementation

- Load workflows, display id/name, open editor link, loading/empty/error states and explicit refresh.

### Acceptance

- List/empty/error/navigation tests pass.

---

## M7-WF-011 — Create Workflow Flow

### Dependencies

```text
M7-WF-010
```

### Owned Files

```text
frontend/src/features/workflows/NewWorkflowForm.tsx
frontend/src/features/workflows/NewWorkflowForm.css
frontend/src/features/workflows/NewWorkflowForm.test.tsx
frontend/src/features/workflows/WorkflowListPage.tsx
```

### Implementation

- Add deterministic create form for workflow id, name and optional description. Initial workflow has empty tasks/edges. Validate nonblank id/name before POST. Navigate to editor only after successful persistence.

### Acceptance

- Validation, successful create and API error tests pass.

---

## M7-EDIT-012 — Editor Graph Domain Mapping

### Dependencies

```text
M7-WF-011
```

### Owned Files

```text
frontend/src/features/editor/graphModel.ts
frontend/src/features/editor/graphModel.test.ts
```

### Implementation

- Define UI graph types and pure conversion WorkflowDefinition <-> editor nodes/edges. Preserve all task execution fields. Dependencies and Edge objects must serialize consistently.

### Acceptance

- Round-trip fixture equality passes; no task field is lost.

---

## M7-EDIT-013 — Editor Reducer & Dirty State

### Dependencies

```text
M7-EDIT-012
```

### Owned Files

```text
frontend/src/features/editor/editorState.ts
frontend/src/features/editor/editorState.test.ts
```

### Implementation

- Pure reducer for load, add/remove/update task, connect/disconnect edge, selection, mark-saved. Track dirty flag and selected task id. No API calls in reducer.

### Acceptance

- Reducer matrix and immutable-state tests pass.

---

## M7-EDIT-014 — React Flow Canvas Bootstrap

### Dependencies

```text
M7-EDIT-013
```

### Owned Files

```text
frontend/src/features/editor/WorkflowCanvas.tsx
frontend/src/features/editor/WorkflowCanvas.css
frontend/src/features/editor/WorkflowCanvas.test.tsx
```

### Implementation

- Render @xyflow/react canvas from editor state with Background, Controls and fit-view. Keep editor domain IDs stable.

### Acceptance

- Fixture nodes/edges render and canvas can mount under jsdom.

---

## M7-EDIT-015 — Task Node Visual Component

### Dependencies

```text
M7-EDIT-014
```

### Owned Files

```text
frontend/src/features/editor/TaskNode.tsx
frontend/src/features/editor/TaskNode.css
frontend/src/features/editor/TaskNode.test.tsx
frontend/src/features/editor/WorkflowCanvas.tsx
```

### Implementation

- Custom task node shows task name/id, execution mode, cwd summary and source/target handles. Selection is visually distinct and accessible.

### Acceptance

- Node fields and handles render; selected state test passes.

---

## M7-EDIT-016 — Add Task Node

### Dependencies

```text
M7-EDIT-015
```

### Owned Files

```text
frontend/src/features/editor/EditorToolbar.tsx
frontend/src/features/editor/EditorToolbar.css
frontend/src/features/editor/WorkflowCanvas.tsx
frontend/src/features/editor/editorState.ts
frontend/src/features/editor/EditorToolbar.test.tsx
```

### Implementation

- Toolbar action adds a deterministic locally unique task with valid defaults and visible canvas position. No backend call until Save.

### Acceptance

- Add action creates one node and marks editor dirty.

---

## M7-EDIT-017 — Node Selection & Inspector Shell

### Dependencies

```text
M7-EDIT-016
```

### Owned Files

```text
frontend/src/features/editor/TaskInspector.tsx
frontend/src/features/editor/TaskInspector.css
frontend/src/features/editor/WorkflowEditorLayout.tsx
frontend/src/features/editor/WorkflowEditorLayout.css
frontend/src/features/editor/TaskInspector.test.tsx
```

### Implementation

- Create canvas + inspector split layout. Clicking a task selects it; empty selection shows guidance.

### Acceptance

- Selection and empty inspector tests pass.

---

## M7-EDIT-018 — Task Identity, Name & CWD Editing

### Dependencies

```text
M7-EDIT-017
```

### Owned Files

```text
frontend/src/features/editor/TaskInspector.tsx
frontend/src/features/editor/fields/TaskBasicsFields.tsx
frontend/src/features/editor/fields/TaskBasicsFields.test.tsx
```

### Implementation

- Edit stable task id, display name and cwd. Reject blank values and duplicate task IDs. Changing an ID must update associated edges/dependency references deterministically.

### Acceptance

- Rename/duplicate/edge-reference tests pass.

---

## M7-EDIT-019 — Full Prompt Editor

### Dependencies

```text
M7-EDIT-018
```

### Owned Files

```text
frontend/src/features/editor/fields/PromptField.tsx
frontend/src/features/editor/fields/PromptField.css
frontend/src/features/editor/TaskInspector.tsx
frontend/src/features/editor/fields/PromptField.test.tsx
```

### Implementation

- Multiline prompt editor with preserved whitespace and large-text usability. No prompt rewriting/summarization.

### Acceptance

- Exact prompt round-trip including newlines passes.

---

## M7-EDIT-020 — Model & Reasoning Configuration

### Dependencies

```text
M7-EDIT-019
```

### Owned Files

```text
frontend/src/features/editor/fields/ModelFields.tsx
frontend/src/features/editor/TaskInspector.tsx
frontend/src/features/editor/fields/ModelFields.test.tsx
```

### Implementation

- Edit optional model and reasoning_effort as explicit user values. Empty values serialize to null; UI does not invent defaults not present in domain data.

### Acceptance

- Null/value serialization tests pass.

---

## M7-EDIT-021 — Sandbox & Approval Configuration

### Dependencies

```text
M7-EDIT-020
```

### Owned Files

```text
frontend/src/features/editor/fields/ExecutionFields.tsx
frontend/src/features/editor/TaskInspector.tsx
frontend/src/features/editor/fields/ExecutionFields.test.tsx
```

### Implementation

- Expose sandbox enum and optional approval_mode. Preserve backend-supported string values and defaults.

### Acceptance

- All sandbox values and null approval round-trip.

---

## M7-EDIT-022 — Timeout & Retry Policy Editing

### Dependencies

```text
M7-EDIT-021
```

### Owned Files

```text
frontend/src/features/editor/fields/RetryFields.tsx
frontend/src/features/editor/TaskInspector.tsx
frontend/src/features/editor/fields/RetryFields.test.tsx
```

### Implementation

- Edit timeout_seconds optional positive integer and retry_policy.max_attempts >=1. No automatic retry semantics are invented in UI.

### Acceptance

- Boundary validation and serialization pass.

---

## M7-EDIT-023 — Execution Mode & Continue-Thread Editing

### Dependencies

```text
M7-EDIT-022
```

### Owned Files

```text
frontend/src/features/editor/fields/ContinuationFields.tsx
frontend/src/features/editor/TaskInspector.tsx
frontend/src/features/editor/fields/ContinuationFields.test.tsx
```

### Implementation

- Switch NEW_THREAD/CONTINUE_THREAD. CONTINUE_THREAD requires explicit continue_from_task_id chosen from another task. NEW_THREAD clears continuation source.

### Acceptance

- Mode transition and required-source tests pass.

---

## M7-EDIT-024 — Connect Dependency Edges

### Dependencies

```text
M7-EDIT-023
```

### Owned Files

```text
frontend/src/features/editor/WorkflowCanvas.tsx
frontend/src/features/editor/editorState.ts
frontend/src/features/editor/editorState.test.ts
```

### Implementation

- React Flow connect action creates explicit dependency edge and updates target dependencies. Reject self-edge and exact duplicate edge client-side.

### Acceptance

- Connect/self/duplicate tests pass.

---

## M7-EDIT-025 — Delete Edges

### Dependencies

```text
M7-EDIT-024
```

### Owned Files

```text
frontend/src/features/editor/WorkflowCanvas.tsx
frontend/src/features/editor/editorState.ts
frontend/src/features/editor/editorState.test.ts
```

### Implementation

- Deleting an edge removes matching target dependency and leaves unrelated dependencies unchanged.

### Acceptance

- Single/multiple edge deletion tests pass.

---

## M7-EDIT-026 — Delete Task Nodes Safely

### Dependencies

```text
M7-EDIT-025
```

### Owned Files

```text
frontend/src/features/editor/EditorToolbar.tsx
frontend/src/features/editor/editorState.ts
frontend/src/features/editor/TaskInspector.tsx
frontend/src/features/editor/editorState.test.ts
```

### Implementation

- Delete selected task only after explicit confirmation UI. Remove incident edges and dependency references. Clear invalid continue_from_task_id references and surface validation afterward.

### Acceptance

- Node deletion cleanup matrix passes.

---

## M7-EDIT-027 — Client Graph Validation

### Dependencies

```text
M7-EDIT-026
```

### Owned Files

```text
frontend/src/features/editor/validation.ts
frontend/src/features/editor/validation.test.ts
```

### Implementation

- Pure editor preflight validation: unique IDs, nonblank required fields, dependency targets exist, edge/dependency consistency, duplicate edges, self edges, cycle detection, continuation source exists/is not self. Backend remains authoritative on save.

### Acceptance

- Valid DAG and each invalid class tested.

---

## M7-EDIT-028 — Validation Summary UI

### Dependencies

```text
M7-EDIT-027
```

### Owned Files

```text
frontend/src/features/editor/ValidationPanel.tsx
frontend/src/features/editor/ValidationPanel.css
frontend/src/features/editor/WorkflowEditorLayout.tsx
frontend/src/features/editor/ValidationPanel.test.tsx
```

### Implementation

- Display deterministic validation issues with task/edge references. Clicking a task issue selects that node. Save disabled while blocking issues exist.

### Acceptance

- Issue rendering, selection and Save-disable tests pass.

---

## M7-EDIT-029 — Workflow Metadata Editing

### Dependencies

```text
M7-EDIT-028
```

### Owned Files

```text
frontend/src/features/editor/WorkflowMetadataPanel.tsx
frontend/src/features/editor/WorkflowMetadataPanel.css
frontend/src/features/editor/WorkflowEditorLayout.tsx
frontend/src/features/editor/WorkflowMetadataPanel.test.tsx
```

### Implementation

- Edit workflow name and optional description; workflow id remains stable on existing workflow.

### Acceptance

- Metadata update and dirty-state tests pass.

---

## M7-EDIT-030 — Workflow Serialization

### Dependencies

```text
M7-EDIT-029
```

### Owned Files

```text
frontend/src/features/editor/serialize.ts
frontend/src/features/editor/serialize.test.ts
```

### Implementation

- Create exact WorkflowDefinition payload from editor state. Stable ordering: nodes in current editor order, edges deterministic by source then target. Derive task.dependencies from explicit edges exactly once.

### Acceptance

- Golden payload tests pass.

---

## M7-EDIT-031 — Save Existing Workflow

### Dependencies

```text
M7-EDIT-030
```

### Owned Files

```text
frontend/src/features/editor/SaveWorkflowButton.tsx
frontend/src/features/editor/SaveWorkflowButton.test.tsx
frontend/src/features/editor/WorkflowEditorLayout.tsx
```

### Implementation

- PUT existing workflow after local validation. Disable duplicate submissions. On success mark editor clean; on failure keep dirty state and surface API error.

### Acceptance

- Success/double-click/error tests pass.

---

## M7-EDIT-032 — Load Existing Workflow Editor Page

### Dependencies

```text
M7-EDIT-031
```

### Owned Files

```text
frontend/src/features/editor/WorkflowEditorPage.tsx
frontend/src/features/editor/WorkflowEditorPage.test.tsx
frontend/src/app/router.tsx
```

### Implementation

- GET workflow by route id, convert to editor state and render editor. Handle loading/404/other errors without losing navigation shell.

### Acceptance

- Load, 404 and API error tests pass.

---

## M7-EDIT-033 — Unsaved Changes Indicator

### Dependencies

```text
M7-EDIT-032
```

### Owned Files

```text
frontend/src/features/editor/UnsavedIndicator.tsx
frontend/src/features/editor/WorkflowEditorLayout.tsx
frontend/src/features/editor/UnsavedIndicator.test.tsx
```

### Implementation

- Show Saved/Unsaved state. Browser beforeunload warning only while dirty. Do not create custom router blocking complexity in this task.

### Acceptance

- Dirty/saved and beforeunload registration tests pass.

---

## M7-EDIT-034 — Editor Keyboard Operations

### Dependencies

```text
M7-EDIT-033
```

### Owned Files

```text
frontend/src/features/editor/useEditorShortcuts.ts
frontend/src/features/editor/WorkflowEditorLayout.tsx
frontend/src/features/editor/useEditorShortcuts.test.tsx
```

### Implementation

- Implement Ctrl/Cmd+S Save, Delete/Backspace selected node only when focus is not inside an editable field, Escape clears selection.

### Acceptance

- Shortcut focus-safety tests pass.

---

## M7-EDIT-035 — Canvas Navigation & View Controls

### Dependencies

```text
M7-EDIT-034
```

### Owned Files

```text
frontend/src/features/editor/WorkflowCanvas.tsx
frontend/src/features/editor/WorkflowCanvas.css
frontend/src/features/editor/WorkflowCanvas.test.tsx
```

### Implementation

- Add MiniMap, fit-view action and explicit zoom controls using React Flow primitives. No custom graph layout algorithm.

### Acceptance

- Controls render and fit action is invokable.

---

## M7-EDIT-036 — Editor Empty State & Onboarding Hint

### Dependencies

```text
M7-EDIT-035
```

### Owned Files

```text
frontend/src/features/editor/EditorEmptyState.tsx
frontend/src/features/editor/EditorEmptyState.css
frontend/src/features/editor/WorkflowEditorLayout.tsx
frontend/src/features/editor/EditorEmptyState.test.tsx
```

### Implementation

- For empty workflow show concise instructions: Add Task, edit Prompt/CWD, connect dependencies, Save, Run. One action adds first node.

### Acceptance

- Empty/non-empty states tested.

---

## M7-EDIT-037 — Editor Regression Matrix

### Dependencies

```text
M7-EDIT-036
```

### Owned Files

```text
frontend/src/features/editor/WorkflowEditorMatrix.test.tsx
```

### Implementation

- Test create 4-node fork/join, rename node, connect/disconnect, delete node, continuation config, invalid cycle, save serialization and reload round-trip using mocks.

### Acceptance

- Full editor matrix passes without backend process.

---

## M7-RUN-038 — Run API Resource Layer

### Dependencies

```text
M7-EDIT-037
```

### Owned Files

```text
frontend/src/features/runs/api.ts
frontend/src/features/runs/api.test.ts
```

### Implementation

- Implement start run, list/get run, list/get tasks and attempts over public M6 API.

### Acceptance

- Endpoint mapping and ApiError propagation tests pass.

---

## M7-RUN-039 — Start Run from Workflow Editor

### Dependencies

```text
M7-RUN-038
```

### Owned Files

```text
frontend/src/features/runs/StartRunButton.tsx
frontend/src/features/runs/StartRunButton.test.tsx
frontend/src/features/editor/WorkflowEditorLayout.tsx
```

### Implementation

- Run action allowed only when editor is saved and valid. POST run returns run_id and navigates to run detail. Handle ACTIVE_RUN conflict explicitly.

### Acceptance

- Saved/dirty/invalid/success/conflict tests pass.

---

## M7-RUN-040 — Run History List Page

### Dependencies

```text
M7-RUN-039
```

### Owned Files

```text
frontend/src/features/runs/RunListPage.tsx
frontend/src/features/runs/RunListPage.css
frontend/src/features/runs/RunListPage.test.tsx
frontend/src/app/router.tsx
```

### Implementation

- List durable runs with workflow id, status, created_at and link to detail. Add optional workflow_id filter from URL query.

### Acceptance

- List/filter/empty/error tests pass.

---

## M7-RUN-041 — Run Detail Page Foundation

### Dependencies

```text
M7-RUN-040
```

### Owned Files

```text
frontend/src/features/runs/RunDetailPage.tsx
frontend/src/features/runs/RunDetailPage.css
frontend/src/features/runs/RunDetailPage.test.tsx
frontend/src/app/router.tsx
```

### Implementation

- Load run detail and task snapshot. Show run status, workflow id, creation time and task list. Handle 404.

### Acceptance

- Success/loading/404 tests pass.

---

## M7-RUN-042 — Run DAG Read-only Visualization

### Dependencies

```text
M7-RUN-041
```

### Owned Files

```text
frontend/src/features/runs/RunGraph.tsx
frontend/src/features/runs/RunGraph.css
frontend/src/features/runs/RunGraph.test.tsx
frontend/src/features/runs/RunDetailPage.tsx
```

### Implementation

- Render immutable run.snapshot DAG with React Flow in read-only mode. No node/edge editing. Match task definitions by task_id.

### Acceptance

- Snapshot graph renders and editing gestures are disabled.

---

## M7-RUN-043 — Task Status Visual Mapping

### Dependencies

```text
M7-RUN-042
```

### Owned Files

```text
frontend/src/features/runs/status.ts
frontend/src/features/runs/RunTaskNode.tsx
frontend/src/features/runs/RunTaskNode.css
frontend/src/features/runs/status.test.ts
```

### Implementation

- Map every canonical TaskStatus to label/presentation token. Unknown status fails visibly as UNKNOWN instead of guessed success.

### Acceptance

- All canonical states plus unknown case tested.

---

## M7-RUN-044 — Run Graph Status Overlay

### Dependencies

```text
M7-RUN-043
```

### Owned Files

```text
frontend/src/features/runs/RunGraph.tsx
frontend/src/features/runs/RunTaskNode.tsx
frontend/src/features/runs/RunGraph.test.tsx
```

### Implementation

- Decorate run nodes using durable TaskRun status. Preserve snapshot node identity and thread/turn references.

### Acceptance

- Mixed-state DAG rendering tests pass.

---

## M7-RUN-045 — Run WebSocket State Hook

### Dependencies

```text
M7-RUN-044
```

### Owned Files

```text
frontend/src/features/runs/useRunStream.ts
frontend/src/features/runs/useRunStream.test.ts
```

### Implementation

- Wrap WebSocket client for one run. Maintain task snapshot and latest event cursor. Clean up on unmount/run change. No state changes are sent to backend.

### Acceptance

- snapshot/event/cleanup tests pass.

---

## M7-RUN-046 — Live Task Snapshot Application

### Dependencies

```text
M7-RUN-045
```

### Owned Files

```text
frontend/src/features/runs/RunDetailPage.tsx
frontend/src/features/runs/useRunStream.ts
frontend/src/features/runs/RunDetailPage.test.tsx
```

### Implementation

- Apply WebSocket snapshot messages to run graph/task list. REST initial load remains fallback/source for first render.

### Acceptance

- PENDING→RUNNING→SUCCESS UI transition test passes.

---

## M7-RUN-047 — Durable Event Log Panel

### Dependencies

```text
M7-RUN-046
```

### Owned Files

```text
frontend/src/features/runs/EventLog.tsx
frontend/src/features/runs/EventLog.css
frontend/src/features/runs/EventLog.test.tsx
frontend/src/features/runs/RunDetailPage.tsx
```

### Implementation

- Display persisted events in arrival order with timestamp, type, task/attempt references and compact JSON payload disclosure. No SDK object assumptions.

### Acceptance

- Ordering and payload rendering tests pass.

---

## M7-RUN-048 — WebSocket Cursor Reconnect

### Dependencies

```text
M7-RUN-047
```

### Owned Files

```text
frontend/src/features/runs/useRunStream.ts
frontend/src/features/runs/useRunStream.test.ts
```

### Implementation

- On unexpected close while run is nonterminal, reconnect with last acknowledged event id using bounded deterministic backoff. Do not reconnect after explicit unmount/terminal run.

### Acceptance

- Cursor, no-duplication, terminal and cleanup tests pass with fake timers.

---

## M7-RUN-049 — Task Detail Drawer

### Dependencies

```text
M7-RUN-048
```

### Owned Files

```text
frontend/src/features/runs/TaskRunDrawer.tsx
frontend/src/features/runs/TaskRunDrawer.css
frontend/src/features/runs/TaskRunDrawer.test.tsx
frontend/src/features/runs/RunGraph.tsx
```

### Implementation

- Selecting run node opens task detail: task id, status, thread_id, turn_id, created_at. Missing optional IDs render clearly.

### Acceptance

- Selection/details/missing metadata tests pass.

---

## M7-RUN-050 — Attempt History in Task Drawer

### Dependencies

```text
M7-RUN-049
```

### Owned Files

```text
frontend/src/features/runs/AttemptHistory.tsx
frontend/src/features/runs/AttemptHistory.test.tsx
frontend/src/features/runs/TaskRunDrawer.tsx
```

### Implementation

- Load attempts lazily for selected task. Show immutable attempt id/status/thread/turn/time in API order.

### Acceptance

- Loading/history/empty/error tests pass.

---

## M7-RUN-051 — Open in Codex Action

### Dependencies

```text
M7-RUN-050
```

### Owned Files

```text
frontend/src/features/runs/OpenInCodex.tsx
frontend/src/features/runs/OpenInCodex.test.tsx
frontend/src/features/runs/TaskRunDrawer.tsx
```

### Implementation

- When thread_id exists expose explicit codex://threads/{encoded-thread-id} link. No Desktop private DB/config access. When absent show unavailable. Automated tests verify URI only; manual desktop opening is deferred to desktop/manual UX milestone.

### Acceptance

- Exact URI, encoding and missing-thread tests pass.

---

## M7-RUN-052 — Failure & Needs-Attention Presentation

### Dependencies

```text
M7-RUN-051
```

### Owned Files

```text
frontend/src/features/runs/TaskStateNotice.tsx
frontend/src/features/runs/TaskStateNotice.css
frontend/src/features/runs/TaskRunDrawer.tsx
frontend/src/features/runs/TaskStateNotice.test.tsx
```

### Implementation

- Present FAILED, INTERRUPTED, BLOCKED and NEEDS_ATTENTION distinctly with non-speculative explanation. Do not expose Retry/Pause/Resume controls yet; those belong to M8 human-in-the-loop/runtime control work.

### Acceptance

- Each state renders deterministic copy and no unsupported action button.

---

## M7-RUN-053 — Run Completion Summary

### Dependencies

```text
M7-RUN-052
```

### Owned Files

```text
frontend/src/features/runs/RunSummaryPanel.tsx
frontend/src/features/runs/RunSummaryPanel.test.tsx
frontend/src/features/runs/RunDetailPage.tsx
```

### Implementation

- Summarize task status counts and terminal run result from durable API data only. No inference that SUCCESS implies code correctness.

### Acceptance

- Mixed counts and terminal/nonterminal tests pass.

---

## M7-NAV-054 — Workflow-to-Run History Navigation

### Dependencies

```text
M7-RUN-053
```

### Owned Files

```text
frontend/src/features/workflows/WorkflowListPage.tsx
frontend/src/features/editor/WorkflowEditorLayout.tsx
frontend/src/features/runs/RunListPage.tsx
frontend/src/features/runs/RunDetailPage.tsx
frontend/src/features/runs/navigation.test.tsx
```

### Implementation

- Add consistent links among workflow list/editor, filtered run history and run detail/back-to-workflow.

### Acceptance

- Cross-page navigation and URL filter tests pass.

---

## M7-UX-055 — Accessible Interaction Pass

### Dependencies

```text
M7-NAV-054
```

### Owned Files

```text
frontend/src/**/*.tsx
frontend/src/**/*.css
frontend/src/ux/accessibility.test.tsx
```

### Implementation

- Add semantic labels, keyboard-focus visibility, button/input labels, dialog roles and status text where already implemented. Do not redesign UI. Ensure canvas-adjacent controls remain reachable.

### Acceptance

- Focused accessibility interaction tests pass; typecheck/lint remain green.

---

## M7-INTEGRATE-056 — Visual DAG UI Integration & Repair

### Dependencies

```text
M7-UX-055
```

### Owned Files

```text
frontend/**
```

### Implementation

- Run the complete M7 user flow with mocked M6 API/WebSocket: list workflows → create → edit multi-node DAG → validate → save → reload → start run → navigate run detail → receive snapshots/events → inspect attempt → open Codex URI → terminal summary. This is a bounded repair task: fix any M7 implementation defect within frontend/** but do not alter backend contracts or architecture.

### Acceptance

- Integrated user-flow test passes; npm test/typecheck/lint/build pass.

---

## M7-GATE-057 — M7 Acceptance Matrix & Backend Regression

### Dependencies

```text
M7-INTEGRATE-056
```

### Owned Files

```text
frontend/**
backend/tests/api/**
backend/tests/integration/**
```

### Implementation

- Execute and, only within owned test/frontend files, repair M7 contract issues. Matrix: app routing; workflow create/get/update/list; DAG node add/edit/delete; edge connect/delete; cycle validation; full Prompt/CWD/config preservation; save/reload; start run; run history; read-only run DAG; all task statuses; WS snapshot/events; reconnect cursor; attempt history; failure/needs-attention display; Open-in-Codex URI; keyboard basics; empty/error/loading states; M6 API contract regressions; complete non-live backend regression. Do not weaken tests or change production backend semantics.

### Acceptance

- All frontend tests, build, typecheck, lint and complete non-live backend tests pass.

---

## M7-REPORT-058 — Visual DAG UI Milestone Report

### Dependencies

```text
M7-GATE-057
```

### Owned Files

```text
docs/visual-dag-ui-test-report.md
```

### Implementation

- Record PASS/FAIL with evidence for: frontend bootstrap; workflow list/create/edit/save; multi-task nodes; complete Prompt; cwd/config fields; dependency edge editing; cycle prevention; run launch; run history; run DAG statuses; WebSocket updates; event log; attempt history; failure/needs-attention presentation; Open-in-Codex URI contract; M6/M5 regression; no master LLM control. On PASS mark M7 complete and leave next_task null unless an authoritative M8 plan exists.

### Acceptance

- Every listed M7 automated gate PASS; report names exact commands/counts and known manual verification deferred to M9 where applicable.

---

# 13. 现在应该怎么开跑

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

# 14. 每次向我反馈 Codex 结果时的格式

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

# 15. 当前技术基线来源

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
