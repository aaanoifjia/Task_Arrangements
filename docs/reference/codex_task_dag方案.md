# Codex Task DAG 调度方案

> 目标：为 ChatGPT / Codex Desktop 建立一个**确定性、可视化、可编排依赖关系**的任务调度工具。  
> 核心原则：**LLM 负责执行任务，调度器不使用 Agent 判断流程。**

---

## 1. 背景

当前使用 Codex 时，常见工作流是：

1. 先让 Codex 做 Plan。
2. Plan 完成后，再创建新的 Codex Task 做 Implementation。
3. 某些任务之间存在明确依赖。
4. 后置任务的 Prompt 已经可以提前准备好。
5. 但后置 Task 不能提前全部创建，只能在前置 Task 完成后再创建并发送 Prompt。
6. 目前需要人工等待前置任务结束，再进入下一个 Task 并手动发送。

目标是消除这个人工等待过程。

---

## 2. 核心需求

### 2.1 确定性

不使用“总控 Agent”决定下一步。

任务流完全由显式依赖关系控制，例如：

```text
        ┌→ Backend ─┐
Setup ──┤            ├→ Test
        └→ Frontend ┘
```

规则：

```text
只有当一个 Task 的全部 dependencies 都为 SUCCESS 时，
该 Task 才进入 READY 状态。
```

Agent 不参与流程判断。

---

### 2.2 延迟创建 Codex Task

不能要求用户提前把所有 Codex Task 都创建好。

调度器只提前保存：

- Task 名称
- Prompt
- 项目路径 / cwd
- 模型
- Reasoning Effort
- Sandbox / Approval 配置
- Dependencies

例如：

```json
{
  "id": "backend",
  "name": "实现 Backend",
  "cwd": "D:\\project",
  "prompt": "这里保存完整任务说明……",
  "dependsOn": ["database"]
}
```

此时 Codex 中不创建实际 Task。

等 `database` 成功后：

```text
dependency SUCCESS
↓
thread/start
↓
创建新的 Codex Thread
↓
turn/start
↓
发送完整 Prompt
↓
Codex 开始执行
```

---

## 3. 技术结论

### 3.1 不再使用 Automa 作为主方案

Automa 更适合：

- ChatGPT Web
- 浏览器标签页
- DOM 自动化

但核心场景是：

- ChatGPT Desktop
- Codex Desktop
- 新建 Codex Task
- 自动发送完整 Prompt

因此浏览器自动化不是最佳路径。

---

### 3.2 推荐使用 Codex App Server / SDK

Codex 当前已经提供适合外部程序控制的能力。

核心生命周期：

```text
initialize
↓
thread/start
↓
获得 thread.id
↓
turn/start
↓
发送完整 Prompt
↓
监听执行事件
↓
turn/completed
```

因此可以实现：

```text
前置 Task 完成
↓
Scheduler 解锁后置 Task
↓
此时才创建新的 Codex Thread
↓
自动发送该 Task 的完整 Prompt
↓
Codex 开始工作
```

这不需要模拟点击 UI。

---

## 4. 为什么 App Server 比 Desktop RPA 更合适

桌面自动化通常需要：

```text
寻找窗口
↓
点击按钮
↓
模拟键盘
↓
观察 UI
↓
猜测任务是否完成
```

容易受到 UI 更新影响。

Codex App Server 则可以直接得到明确状态：

```text
turn started
↓
running
↓
turn/completed
```

或者：

```text
failed
interrupted
approval required
user input required
```

因此任务调度可以建立在真实协议事件上，而不是视觉判断。

---

## 5. 推荐状态机

建议第一版使用以下状态：

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
```

### 状态转换

```text
PENDING
↓
检查 dependencies

全部 SUCCESS
↓
READY

READY
↓
Scheduler 启动
↓
STARTING

STARTING
↓
thread/start + turn/start 成功
↓
RUNNING
```

运行过程中：

```text
RUNNING
├─ turn/completed(completed) → SUCCESS
├─ turn/completed(failed) → FAILED
├─ interrupted → INTERRUPTED
└─ approval / user input → NEEDS_ATTENTION
```

---

## 6. 依赖规则

核心规则：

```text
READY =
所有 dependencies.status === SUCCESS
```

伪代码：

```python
for task in tasks:
    if task.status in ["PENDING", "BLOCKED"]:
        if all(dep.status == "SUCCESS" for dep in task.dependencies):
            task.status = "READY"
```

Scheduler：

```python
while running_count < concurrency:
    task = next_ready_task()

    if task is None:
        break

    start_task(task)
```

---

## 7. 失败策略

默认必须采用 Fail-Closed。

例如：

```text
A → B
A → C
```

如果：

```text
A = FAILED
```

则：

```text
B = BLOCKED
C = BLOCKED
```

不能让后续 Task 自动继续。

UI 提供：

```text
[Retry]
[Mark Success]
[Skip]
```

只有用户明确操作后，才继续释放下游 Task。

---

## 8. Prompt 是真正的任务内容

`turn/start` 发送的是完整用户输入，而不是简单的：

```text
开始
```

因此 Task 可以保存完整 Prompt，例如：

```text
Task: 修复 SkyRoom 比例

cwd:
D:\fiona\game\SkyRoom

Prompt:

只修改当前 Level：
01_skyroom_1

目标：
恢复 Character 默认 Scale，
然后以 Character 为基准，
统一调整当前场景中的 Actor 比例。

要求：
1. 不创建备份 Map
2. 使用现有 Git version control
3. 保持整体场景比例关系
...
```

依赖满足后，Scheduler 原样发送给 Codex。

---

## 9. 支持 Plan → Implementation

一个典型工作流：

```text
Planning
Read Only
High Reasoning
       ↓
Implementation
Workspace Write
Medium / High Reasoning
       ↓
Verification
Read Only
High Reasoning
```

有两种执行模式。

### 模式 A：New Task

每个节点创建独立 Codex Thread：

```text
Plan Thread
↓
Implementation Thread
↓
Verification Thread
```

适合需要任务隔离的场景。

### 模式 B：Continue Existing Task

继续同一个 Thread：

```text
thread/start
↓
Plan turn
↓
turn completed
↓
继续同一 thread
↓
Implementation turn
```

未来节点可增加：

```text
Execution Mode

○ New Codex Task
● Continue Task X
```

---

## 10. 每个节点建议保存的配置

```yaml
id: backend
name: Implement Backend

cwd: D:\project

prompt: |
  完成 Backend API。
  ...

depends_on:
  - database

execution_mode: new_thread

model: default
reasoning_effort: high

sandbox: workspace-write
approval_policy: default

timeout: 7200
retry_count: 0
```

---

## 11. 推荐 UI

长期目标是一个图形化 DAG 编辑器：

```text
┌──────────────────────────────────────┐
│ Codex Flow                           │
│                                      │
│      ┌──────────────┐                │
│      │ DB Migration │ ✓              │
│      └──────┬───────┘                │
│             │                        │
│       ┌─────┴───────┐                │
│       ↓             ↓                │
│ ┌──────────┐   ┌──────────┐         │
│ │ Backend  │   │ Frontend │         │
│ │ Running  │   │ Ready    │         │
│ └────┬─────┘   └────┬─────┘         │
│      │              │                │
│      └──────┬───────┘                │
│             ↓                        │
│        ┌────────┐                    │
│        │ Tests  │                    │
│        │Blocked │                    │
│        └────────┘                    │
│                                      │
│ Concurrency: 1        ▶ Run          │
└──────────────────────────────────────┘
```

建议后期使用 React Flow。

---

## 12. Scheduler 自己成为 Task Sidebar

目前一个已知风险：

外部通过 App Server 创建的 Codex Thread，
不一定能立刻正确出现在 Codex Desktop 的项目侧栏中。

因此不能把 Desktop Sidebar 当作唯一任务列表。

更合理的设计是：

```text
Codex Flow
=
真正的 Task Dashboard
```

每个 Task 显示：

```text
Backend

Status:
RUNNING

Thread ID:
019f...

[Open in Codex]
```

---

## 13. Desktop 集成

外部创建的 Thread 可以保留其 `thread_id`。

未来可以尝试通过：

```text
codex://threads/<thread-id>
```

从调度器直接打开对应 Codex Thread。

因此 Desktop 主要承担：

- 查看 Codex 执行详情
- 人工介入
- 与 Codex 继续交互

而不是承担调度逻辑。

---

## 14. NEEDS_ATTENTION

Codex 执行过程中可能需要：

- Approval
- User Input
- Permission
- Tool confirmation

因此 Task 可能进入：

```text
NEEDS_ATTENTION
```

UI 示例：

```text
Task: Backend

Status:
NEEDS ATTENTION

Codex requests approval:

Run:
npm install

[Approve]
[Deny]

[Open in Codex]
```

这样用户不需要不断检查所有 Codex Task。

---

## 15. Concurrency

Scheduler 应支持最大并发数。

例如：

```text
Concurrency = 1
```

表示严格串行。

```text
Concurrency = 2
```

表示最多两个 Codex Task 同时运行。

例如：

```text
        ┌→ Backend ─┐
Setup ──┤            ├→ Test
        └→ Frontend ┘
```

如果：

```text
Concurrency = 2
```

Setup 完成后：

```text
Backend
Frontend
```

可以同时启动。

Test 必须等待二者都 SUCCESS。

---

## 16. 推荐系统架构

第一版：

```text
┌───────────────────┐
│ Task Definitions  │
│ JSON / SQLite     │
└─────────┬─────────┘
          │
          ↓
┌───────────────────┐
│ DAG Scheduler     │
└─────────┬─────────┘
          │
          ↓
┌───────────────────┐
│ Codex Adapter     │
│ App Server / SDK  │
└─────────┬─────────┘
          │
          ↓
┌───────────────────┐
│ Codex             │
└───────────────────┘
```

未来：

```text
              Codex Flow UI
                    │
                    ↓
              DAG Scheduler
                    │
       ┌────────────┴────────────┐
       ↓                         ↓
 Codex Adapter             Other Adapter
       │
 App Server / SDK
       │
       ↓
     Codex
```

---

## 17. 第一阶段不要做完整产品

第一步只做一个最小 POC。

文件：

```text
tasks.json
runner.py
README.md
```

`tasks.json`：

```json
[
  {
    "id": "A",
    "cwd": "D:\\test-project",
    "prompt": "Task A prompt",
    "dependsOn": []
  },
  {
    "id": "B",
    "cwd": "D:\\test-project",
    "prompt": "Task B prompt",
    "dependsOn": ["A"]
  }
]
```

目标：

```text
启动 Scheduler
↓
创建 Task A Codex Thread
↓
发送 Prompt A
↓
等待真实 completion event
↓
A = SUCCESS
↓
创建 Task B Codex Thread
↓
发送 Prompt B
↓
等待 completion
↓
B = SUCCESS
```

---

## 18. POC 必须验证的事项

### 验证 1：ChatGPT / Codex 登录

确认 App Server 使用当前 ChatGPT / Codex 登录身份。

目标是不额外建立独立 API 计费工作流。

---

### 验证 2：任务完成事件

确认能够可靠获取：

```text
turn/completed
```

并区分：

```text
completed
failed
interrupted
```

---

### 验证 3：Desktop 打开 Thread

验证：

```text
codex://threads/<thread-id>
```

是否能在当前 Windows 环境打开对应任务。

---

### 验证 4：Desktop Sidebar 同步

观察外部创建的 Thread：

- 是否立即显示
- 是否需要刷新
- 是否需要重启
- 是否可以 Search 找到
- 是否正确归入 Project

这一项不是 Scheduler 成功的硬条件。

---

### 验证 5：Approval

创建一个会触发 Approval 的测试 Task。

确认 Scheduler 能检测：

```text
NEEDS_ATTENTION
```

---

### 验证 6：并发

测试两个无依赖任务：

```text
A
B
```

确保可以同时运行。

---

## 19. 第二阶段

POC 通过后，再开发本地 UI。

推荐技术栈：

```text
Tauri / Electron
+
React
+
React Flow
+
SQLite
+
Codex App Server Adapter
```

如果只做 Windows，也可以采用更轻的本地 Web UI + Python 后端。

---

## 20. 第三阶段

增加：

- 拖拽 DAG
- Task Templates
- Plan → Implementation Template
- Retry
- Manual Override
- Pause / Resume
- Concurrency
- Notification
- Execution History
- Prompt Version
- Duplicate Workflow
- Import / Export JSON
- Project presets
- Open in Codex
- Continue Existing Thread

---

## 21. 不建议第一阶段做的事情

不要一开始实现：

- 多 Agent 调度
- LLM 自动分析依赖
- LLM 自动决定下一任务
- 云端数据库
- 账号系统
- 多用户协作
- Prompt Marketplace
- 复杂权限系统
- Desktop RPA
- 浏览器自动化
- 完整可视化编辑器

第一阶段唯一问题：

> Codex App Server 是否可以稳定完成 dependency → create thread → send prompt → wait completion → trigger next task。

---

## 22. 设计原则

### 原则 1：Orchestrator 不智能

```text
AI = Worker

Scheduler = State Machine
```

---

### 原则 2：所有依赖显式定义

禁止：

```text
“模型认为 B 现在应该开始。”
```

只允许：

```text
dependsOn: ["A"]
```

---

### 原则 3：失败默认阻断

```text
FAILED
↓
Block downstream
```

而不是自动猜测是否继续。

---

### 原则 4：Codex UI 只是 Viewer

核心任务状态存储在 Scheduler。

Codex Desktop 负责：

- 查看
- 人工交互
- Debug

而不是成为工作流数据库。

---

### 原则 5：Prompt 原样发送

Scheduler 不重写 Prompt。

用户保存什么，就发送什么。

---

## 23. 最终目标

最终工具可以实现：

```text
用户：
一次准备好所有任务和 Prompt
↓
绘制依赖关系
↓
点击 Run
```

之后：

```text
Task A
↓
Codex 执行
↓
SUCCESS
↓
自动创建 Task B
↓
发送 Prompt B
↓
Codex 执行
↓
SUCCESS
↓
自动创建 C / D
↓
...
```

用户只有在：

```text
FAILED
NEEDS_ATTENTION
INTERRUPTED
```

时才需要回来处理。

最终体验：

```text
定义任务
+
定义依赖
+
启动

↓

Codex 自动按照确定性 DAG 执行
```

---

## 24. 当前结论

这个方案在技术上可行。

核心能力已经具备：

- 程序化创建 Codex Thread
- 程序化发送完整 Prompt
- 指定 cwd
- 配置模型 / reasoning / sandbox
- 等待真实完成事件
- 检测失败 / interrupted
- 处理 Approval / User Input