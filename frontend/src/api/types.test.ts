import { describe, expect, it } from 'vitest'
import type { StreamMessage, TaskDefinition, WorkflowDefinition } from './types'

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
})
