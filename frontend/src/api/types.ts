export type ExecutionMode = 'NEW_THREAD' | 'CONTINUE_THREAD'
export type SandboxMode = 'read_only' | 'workspace_write' | 'full_access'
export type TaskStatus =
  | 'PENDING'
  | 'READY'
  | 'STARTING'
  | 'RUNNING'
  | 'SUCCESS'
  | 'FAILED'
  | 'BLOCKED'
  | 'CANCELLED'
  | 'INTERRUPTED'
  | 'NEEDS_ATTENTION'
  | 'SKIPPED'

export type Edge = { source_task_id: string; target_task_id: string }

export type RetryPolicy = { max_attempts: number }

export type TaskDefinition = {
  id: string
  name: string
  prompt: string
  cwd: string
  dependencies: string[]
  execution_mode: ExecutionMode
  continue_from_task_id: string | null
  model: string | null
  reasoning_effort: string | null
  sandbox: SandboxMode
  approval_mode: string | null
  timeout_seconds: number | null
  retry_policy: RetryPolicy
}

export type WorkflowDefinition = {
  id: string
  name: string
  description: string | null
  tasks: TaskDefinition[]
  edges: Edge[]
}

export type WorkflowSummary = { id: string; name: string }
export type WorkflowDetail = { workflow: WorkflowDefinition }
export type RunStartResponse = { run_id: string }
export type RunStatus = TaskStatus | 'PENDING'
export type RunSummary = { id: string; workflow_id: string; status: RunStatus; created_at: string }
export type RunDetail = RunSummary & { snapshot: Record<string, unknown> }

export type TaskRunView = {
  id: string
  workflow_run_id: string
  task_id: string
  status: TaskStatus
  thread_id: string | null
  turn_id: string | null
  created_at: string
}

export type AttemptView = {
  id: string
  task_run_id: string
  status: TaskStatus
  thread_id: string | null
  turn_id: string | null
  created_at: string
}

export type EventView = {
  id: string
  workflow_run_id: string | null
  task_run_id: string | null
  attempt_id: string | null
  event_type: string
  payload: Record<string, unknown>
  created_at: string
}

export type ErrorBody = { code: string; message: string }
export type ErrorResponse = { error: ErrorBody }
export type ControlAction = 'PAUSE' | 'RESUME' | 'RETRY' | 'CANCEL' | 'SKIP' | 'MARK_SUCCESS'
export type ManualActionResponse = {
  action: ControlAction
  run_id: string
  task_id: string | null
  accepted: boolean
  previous_status: TaskStatus | null
  status: TaskStatus | null
  retry_requested: boolean
  error_code: string | null
  message: string | null
}
export type RunControlState = {
  run_id: string
  paused: boolean
  paused_at: string | null
}
export type StreamMessage =
  | { kind: 'event'; payload: EventView }
  | { kind: 'snapshot'; payload: { tasks: TaskRunView[] } }
