import type {
  AttemptView, EventView, RunDetail, RunSummary, StreamMessage, TaskRunView,
  WorkflowDefinition, WorkflowDetail, WorkflowSummary,
} from '../api/types'

export const fixtureWorkflow: WorkflowDefinition = {
  id: 'workflow-1', name: 'Example workflow', description: 'Fixture workflow',
  tasks: [
    {
      id: 'A', name: 'First task', prompt: 'Create A', cwd: '.', dependencies: [],
      execution_mode: 'NEW_THREAD', continue_from_task_id: null, model: null,
      reasoning_effort: null, sandbox: 'workspace_write', approval_mode: null,
      timeout_seconds: null, retry_policy: { max_attempts: 1 },
    },
    {
      id: 'B', name: 'Second task', prompt: 'Create B', cwd: '.', dependencies: ['A'],
      execution_mode: 'CONTINUE_THREAD', continue_from_task_id: 'A', model: null,
      reasoning_effort: null, sandbox: 'workspace_write', approval_mode: null,
      timeout_seconds: null, retry_policy: { max_attempts: 2 },
    },
  ],
  edges: [{ source_task_id: 'A', target_task_id: 'B' }],
}

export const fixtureWorkflowSummary: WorkflowSummary = { id: fixtureWorkflow.id, name: fixtureWorkflow.name }
export const fixtureWorkflowDetail: WorkflowDetail = { workflow: fixtureWorkflow }
export const fixtureRunSummary: RunSummary = {
  id: 'run-1', workflow_id: fixtureWorkflow.id, status: 'RUNNING', created_at: '2026-01-01T00:00:00Z',
}
export const fixtureRunDetail: RunDetail = { ...fixtureRunSummary, snapshot: { workflow_id: fixtureWorkflow.id } }
export const fixtureTaskRun: TaskRunView = {
  id: 'task-run-a', workflow_run_id: 'run-1', task_id: 'A', status: 'RUNNING',
  thread_id: 'thread-1', turn_id: 'turn-1', created_at: '2026-01-01T00:00:01Z',
}
export const fixtureAttempt: AttemptView = {
  id: 'attempt-1', task_run_id: fixtureTaskRun.id, status: 'RUNNING',
  thread_id: 'thread-1', turn_id: 'turn-1', created_at: '2026-01-01T00:00:01Z',
}
export const fixtureEvent: EventView = {
  id: 'event-1', workflow_run_id: 'run-1', task_run_id: fixtureTaskRun.id,
  attempt_id: fixtureAttempt.id, event_type: 'TURN_STARTED', payload: {}, created_at: '2026-01-01T00:00:02Z',
}
export const fixtureMessages: StreamMessage[] = [
  { kind: 'event', payload: fixtureEvent },
  { kind: 'snapshot', payload: { tasks: [fixtureTaskRun] } },
]
