import { describe, expect, it } from 'vitest'
import type {
  ManualActionResponse,
  RunControlState,
  StreamMessage,
  TaskDefinition,
  WorkflowDefinition,
} from './types'

describe('public API models', () => {
  it('accepts representative workflow and stream payloads', () => {
    const task: TaskDefinition = {
      id: 'A', name: 'A', prompt: 'run', cwd: '.', dependencies: [],
      execution_mode: 'NEW_THREAD', continue_from_task_id: null, model: null,
      reasoning_effort: null, sandbox: 'workspace_write', approval_mode: null,
      timeout_seconds: null, retry_policy: { max_attempts: 1 },
    }
    const workflow: WorkflowDefinition = {
      id: 'workflow', name: 'Workflow', description: null, tasks: [task], edges: [],
    }
    const message: StreamMessage = { kind: 'snapshot', payload: { tasks: [] } }
    expect(workflow.tasks[0]?.execution_mode).toBe('NEW_THREAD')
    expect(message.kind).toBe('snapshot')
  })

  it('mirrors durable control responses and paused run state', () => {
    const action: ManualActionResponse = {
      action: 'MARK_SUCCESS', run_id: 'run-1', task_id: 'task-1', accepted: true,
      previous_status: 'READY', status: 'SUCCESS', retry_requested: false,
      error_code: null, message: null,
    }
    const control: RunControlState = { run_id: 'run-1', paused: true, paused_at: 'now' }

    expect(action.status).toBe('SUCCESS')
    expect(control.paused).toBe(true)
  })

  it('includes SKIPPED in task statuses', () => {
    const skipped: ManualActionResponse = {
      action: 'SKIP', run_id: 'run-1', task_id: 'task-1', accepted: true,
      previous_status: 'BLOCKED', status: 'SKIPPED', retry_requested: false,
      error_code: null, message: null,
    }

    expect(skipped.status).toBe('SKIPPED')
  })
})
