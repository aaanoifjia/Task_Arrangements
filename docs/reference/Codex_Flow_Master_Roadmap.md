# Codex Flow — Master Roadmap

> 版本：v1.0 Master Roadmap  
> 日期：2026-10-15  
> 定位：后续所有详细任务拆分、Codex 执行 Prompt、开发优先级与验收标准的上层路线参考。  
> 前置方案：`codex_task_dag方案.md`

---

# 0. 最终目标

构建一个 Windows 优先的本地桌面工具（暂定名 **Codex Flow**），让用户提前定义多个 Codex Task 的：

- 完整 Prompt
- 工作目录 / Project
- 模型与 Reasoning Effort
- Sandbox / Approval 策略
- Task 依赖关系
- New Thread / Continue Thread 执行方式

然后由一个**确定性 DAG Scheduler** 自动执行：

```text
定义任务 + 定义依赖
        ↓
       Run
        ↓
依赖满足才真正创建 Codex Task
        ↓
发送完整 Prompt
        ↓
监听真实 Codex completion / failure / interrupt
        ↓
更新 Task 状态
        ↓
确定性释放后续 Task
```

LLM 只负责每个 Task 内部的智能工作。

Scheduler 不使用 LLM 判断：

- 是否开始后续 Task
- Task 之间的依赖
- 是否跳过失败
- 是否重试
- DAG 的控制流

---

# 1. 冻结的总体技术路线

为了避免后期大规模迁移，以下架构从一开始就作为长期结构。

## 1.1 Core / Backend

**Python 3.11+**

原因：

- OpenAI 已发布稳定的 `openai-codex` Python SDK。
- SDK 可以创建 / resume Thread、执行 Turn、监听 Turn completion。
- SDK 自动安装与自身版本匹配的 Codex runtime。
- SDK 可以复用现有 Codex 登录。
- Python 适合编写 Scheduler、状态机、SQLite、测试和快速迭代。

---

## 1.2 Codex Integration

建立稳定接口：

```text
CodexAdapter
```

上层只能依赖 Adapter，不能直接依赖：

- Codex Desktop
- CLI UI
- App Server daemon
- SDK 私有实现
- Desktop SQLite / LevelDB

初始实现：

```text
SdkCodexAdapter
    ↓
openai-codex Python SDK
    ↓
SDK-pinned Codex runtime
```

后续需要人工 Approval / User Input 时，可以在 Adapter 内增加：

```text
AppServerRpcAdapter
    ↓
原生 Codex App Server JSON-RPC
```

Scheduler / DB / UI 不改变。

---

## 1.3 Workflow Engine

自己实现确定性 DAG Scheduler。

不使用：

- LangGraph Agent
- 主控 LLM
- n8n 作为运行核心
- Codex 内置 Queue 作为唯一调度器

原因：

我们需要自己控制：

- dependency
- failure propagation
- concurrency
- retry
- restart recovery
- task creation timing
- workspace lock

---

## 1.4 Persistence

**SQLite**

持久化：

- Workflow Definition
- Task Definition
- Edge
- Workflow Run
- Task Run
- Attempt
- Codex Thread ID
- Codex Turn ID
- 状态事件
- Prompt Snapshot
- 配置 Snapshot

运行中的 Workflow 不能只存在内存中。

---

## 1.5 Local Service

**FastAPI**

职责：

- 给 UI 提供 REST API
- 暴露 workflow/run/task 操作
- WebSocket 推送实时 Task 状态和 Codex events
- 管理 Scheduler 生命周期

UI 不直接操作 Codex。

---

## 1.6 UI

**React + TypeScript + React Flow (`@xyflow/react`)**

职责：

- DAG 画布
- Node 编辑
- 连线 Dependency
- Workflow 保存
- Run 状态展示
- Logs / Event View
- Failure / Retry
- Needs Attention
- Open in Codex

---

## 1.7 Desktop Packaging

最终使用：

**Tauri + Python Sidecar**

结构：

```text
Tauri Desktop Shell
        │
        ├── React UI
        │
        └── Python Backend Sidecar
                │
                ├── Scheduler
                ├── SQLite
                └── CodexAdapter
```

Python Backend 最终打包成 Windows executable，再由 Tauri 作为 sidecar 启动。

---

# 2. 必须长期保持的领域模型

## 2.1 Workflow Definition 与 Workflow Run 分开

Workflow 是模板：

```text
WorkflowDefinition
```

点击 Run 时，生成一次不可变运行快照：

```text
WorkflowRun
```

这样运行过程中即使用户修改画布，也不会改变已经开始的 Run。

---

## 2.2 Task Definition 与 Task Run 分开

TaskDefinition：

```text
name
prompt
cwd
dependencies
model
reasoning_effort
sandbox
execution_mode
```

TaskRun：

```text
status
thread_id
turn_id
attempt
started_at
completed_at
error
```

---

## 2.3 Attempt 单独记录

每一次 Retry 都创建新的 Attempt。

禁止直接覆盖之前失败的数据。

例如：

```text
TaskRun
 ├── Attempt 1 FAILED
 ├── Attempt 2 FAILED
 └── Attempt 3 SUCCESS
```

---

# 3. 固定状态机

核心状态：

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

核心规则：

```text
READY
=
该 Task 所有 dependencies 都是 SUCCESS
```

失败默认 Fail-Closed：

```text
A FAILED
↓
所有依赖 A 的 Task 保持 BLOCKED
```

禁止 Scheduler 自行猜测是否继续。

---

# 4. 关键执行约束

## 4.1 DAG 必须无环

保存 Workflow 前必须执行 cycle detection。

有环则禁止 Run。

---

## 4.2 默认同一 Workspace 只允许一个写任务

即使 DAG 显示两个任务可以并发：

```text
A → B
A → C
```

如果 B 和 C：

```text
cwd = 同一个 Git Repository
sandbox = workspace_write
```

默认不能同时运行。

初始规则：

```text
global concurrency = configurable
per-workspace write concurrency = 1
```

后续如果需要并行写同一个 Repository，使用 Git Worktree Isolation，而不是直接放开锁。

---

## 4.3 Retry 策略

自动 Retry 只用于明确的 transient errors，例如：

- Server busy
- 临时 transport error
- 短暂服务 overload

以下情况默认不自动 Retry：

- Codex task failed
- Prompt / parameter error
- 权限错误
- 用户 interrupt
- 测试失败
- 不明确异常

---

## 4.4 Completion 定义

Scheduler 的技术完成标准：

```text
收到对应 Turn 的 terminal completion event
```

不能使用：

- 时间等待
- UI 按钮消失
- Codex 最终回复文本
- LLM 自己声称完成

注意：

```text
Turn SUCCESS
≠
代码逻辑一定正确
```

业务正确性需要：

- Task Prompt 内测试
或
- 独立 Verification Node

---

# 5. Milestone 总览

```text
M0  Architecture Freeze
 ↓
M1  Codex Execution Spike
 ↓
M2  Codex Adapter Layer
 ↓
M3  Deterministic DAG Engine
 ↓
M4  Persistence & Crash Recovery
 ↓
M5  Headless End-to-End MVP
 ↓
M6  Local API & Runtime Service
 ↓
M7  Visual DAG UI
 ↓
M8  Human-in-the-loop & Reliability
 ↓
M9  Desktop Integration & Packaging
 ↓
M10 Real-world Beta / Hardening
 ↓
V1
```

高级能力放入 Post-V1，不阻塞 V1。

---

# M0 — Architecture Freeze

## 目标

在开始写产品代码之前固定：

- 技术边界
- Domain Model
- Adapter 接口
- 状态机
- 数据模型原则
- V1 Scope
- 验收标准

避免边开发边修改基础架构。

## 关键步骤

### M0.1 建立 Repository

推荐结构：

```text
codex-flow/
├── backend/
├── frontend/
├── desktop/
├── tests/
├── docs/
├── examples/
└── scripts/
```

### M0.2 写 Architecture Decision Records

至少记录：

```text
ADR-001 Python backend
ADR-002 Codex Adapter boundary
ADR-003 SQLite persistence
ADR-004 FastAPI local service
ADR-005 React Flow UI
ADR-006 Tauri desktop shell
ADR-007 deterministic DAG semantics
ADR-008 workspace locking
```

### M0.3 固定 V1 Domain Schema

确定：

- Workflow
- Task
- Edge
- Run
- TaskRun
- Attempt
- Event

### M0.4 固定状态转换表

每个状态：

- 可以从哪里进入
- 可以进入哪里
- 谁可以触发
- 是否 terminal

### M0.5 定义 V1 Acceptance Criteria

最终 V1 必须满足本文件第 15 节。

## 产出

```text
docs/architecture.md
docs/domain-model.md
docs/state-machine.md
docs/adr/
docs/v1-acceptance.md
```

## Milestone 完成标准

后续所有实现任务可以在不改变架构层级的情况下归入明确模块。

---

# M1 — Codex Execution Spike

## 目标

在正式开发 Scheduler 之前，先证明最关键的外部依赖：

> Python 程序能在当前 Windows 机器上通过官方 Codex 能力，创建一个真正的新任务、发送完整 Prompt、获得准确 completion，并继续 / interrupt 该 Thread。

这是整个项目唯一必须最早通过的技术 Gate。

## 关键步骤

### M1.1 安装稳定 Codex Python SDK

验证：

```text
pip install openai-codex
```

检查：

- SDK version
- bundled/pinned runtime version
- Python version

### M1.2 验证认证

确认：

- 可以复用已有 Codex 登录
- 不需要单独 API Key
- 使用的是用户的 ChatGPT/Codex entitlement

记录账户 / runtime 信息，但不保存 token。

### M1.3 创建新 Thread

指定：

- cwd
- sandbox
- model（可选）
- ephemeral / persistence strategy

保存：

```text
thread_id
```

### M1.4 发送真实 Prompt

Prompt 必须实际：

- 读取测试 Repository
- 修改一个文件
- 执行一个简单测试

不是只让模型回复 Hello。

### M1.5 监听 Turn

验证：

```text
RUNNING
↓
turn/completed
↓
completed / failed / interrupted
```

保存：

```text
turn_id
status
final_response
usage
```

### M1.6 Resume

程序退出后重新启动：

```text
thread_resume(thread_id)
```

发送第二条 Prompt。

验证上下文仍存在。

### M1.7 Interrupt

启动一个较长任务，然后程序化 interrupt。

确认最终状态：

```text
INTERRUPTED
```

### M1.8 Desktop Interop Probe

非阻塞 Gate，只记录实际表现：

- 新 Thread 是否出现在 Desktop sidebar
- `codex://threads/<id>` 是否能打开
- 是否需要 Desktop restart
- Windows 当前版本行为

不要修改 Desktop 私有数据库。

### M1.9 Packaging Feasibility Spike

验证 Python SDK + pinned Codex runtime 能否被未来的 backend executable 正确调用。

这里不做正式 Installer，但必须确认没有架构级阻塞。

## 产出

```text
spikes/codex_execution_probe/
docs/codex-compatibility-report.md
docs/windows-desktop-interop.md
tests/live/codex_smoke_test.py
```

兼容性报告至少记录：

```text
Windows version
Codex Desktop version
openai-codex version
Codex runtime version
Auth mode
thread/start ✓/✗
turn/start ✓/✗
completion ✓/✗
resume ✓/✗
interrupt ✓/✗
Desktop deep link ✓/✗
Desktop sidebar sync behavior
```

## Milestone 完成标准

必须确认：

```text
程序化创建 Task
+
发送真实 Prompt
+
收到 terminal status
+
Resume
```

全部可用。

如果失败，停止进入 M2，重新评估 Codex Transport。

---

# M2 — Codex Adapter Layer

## 目标

把 Codex 的所有外部变化封装起来。

Scheduler 永远不直接调用 SDK。

## 关键步骤

### M2.1 定义 CodexAdapter Interface

至少支持：

```text
create_thread()
start_turn()
resume_thread()
interrupt_turn()
get_thread()
stream_events()
set_thread_name()
```

### M2.2 定义统一 Event Model

把 Codex 事件转换成内部事件，例如：

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

### M2.3 实现 SdkCodexAdapter

使用官方稳定 Python SDK。

所有 SDK-specific object 只能存在 Adapter 层。

### M2.4 实现 FakeCodexAdapter

Fake Adapter 可以模拟：

- success
- failed
- interrupted
- slow turn
- overload
- transport disconnect
- retry
- needs attention

后续 Scheduler 测试默认使用 Fake Adapter，不消耗 Codex 额度。

### M2.5 Contract Tests

同一组 Adapter Contract Tests 同时跑：

```text
FakeCodexAdapter
SdkCodexAdapter
```

确保行为一致。

## 产出

```text
backend/codex_adapter/
backend/codex_adapter/interface.py
backend/codex_adapter/sdk_adapter.py
backend/codex_adapter/fake_adapter.py
tests/contracts/test_codex_adapter.py
```

## Milestone 完成标准

删除 / 替换 `SdkCodexAdapter` 时：

```text
Scheduler
Database
UI
```

都不需要修改。

---

# M3 — Deterministic DAG Engine

## 目标

实现不依赖 Codex 的纯确定性 Workflow Engine。

首先只和 FakeCodexAdapter 运行。

## 关键步骤

### M3.1 DAG Validation

实现：

- node id uniqueness
- missing dependency detection
- duplicate edge detection
- cycle detection

### M3.2 Readiness Calculation

核心规则：

```text
ALL parents SUCCESS
→ READY
```

### M3.3 State Machine

所有状态切换必须通过统一 State Transition Service。

禁止代码任意：

```python
task.status = "SUCCESS"
```

### M3.4 Scheduler Loop

实现：

- 找 READY tasks
- 检查 global concurrency
- 检查 workspace lock
- 创建 execution attempt
- 调用 Adapter
- 接收 terminal event
- 更新后续 readiness

### M3.5 Failure Propagation

验证：

```text
A FAILED
→ B BLOCKED
→ C BLOCKED
```

### M3.6 Manual Operations

支持：

- Retry
- Cancel
- Skip
- Mark Success
- Pause Workflow
- Resume Workflow

所有 Manual Override 必须记录 Event Audit。

### M3.7 Continue Thread Mode

Task 支持：

```text
NEW_THREAD
CONTINUE_THREAD
```

Continue Thread 必须引用明确 upstream thread_id。

### M3.8 Concurrency & Workspace Lock

实现：

```text
global concurrency limit
per cwd write lock
per thread active-turn lock
```

## 产出

```text
backend/domain/
backend/scheduler/
tests/unit/test_dag_validation.py
tests/unit/test_state_machine.py
tests/unit/test_scheduler.py
tests/unit/test_concurrency.py
```

以及一个纯 Fake Adapter Demo：

```text
examples/fake_workflow.yaml
```

## Milestone 完成标准

无需 Codex 网络连接即可通过完整 DAG 测试矩阵。

---

# M4 — Persistence & Crash Recovery

## 目标

保证程序关闭 / 崩溃 / Windows 重启后不会：

- 丢失 Workflow
- 重复创建 Task
- 重复发送同一个 Prompt
- 错误释放下游 Task

这是从 Demo 变成真正工具的关键 Milestone。

## 关键步骤

### M4.1 SQLite Schema

至少包含：

```text
workflows
tasks
edges

workflow_runs
task_runs
attempts

events
settings
```

### M4.2 Snapshot

点击 Run 时保存：

```text
Workflow Definition Snapshot
Prompt Snapshot
Task Config Snapshot
Dependency Snapshot
```

之后编辑 Workflow 不影响正在运行的 Run。

### M4.3 Transactional State Transitions

关键过程：

```text
READY → STARTING
```

必须先持久化 Attempt，再调用 Codex。

防止：

```text
Codex 已启动
但 DB 不知道
```

### M4.4 External IDs

保存：

```text
thread_id
turn_id
client request / attempt identity
```

### M4.5 Recovery Reconciliation

启动程序时扫描：

```text
STARTING
RUNNING
NEEDS_ATTENTION
```

逐个向 CodexAdapter 查询真实状态。

### M4.6 Duplicate Protection

确保程序 crash 后不会重新执行已经启动的 attempt。

### M4.7 Migration System

从第一版数据库开始就加入：

```text
schema_version
migration scripts