import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { TaskDefinition, WorkflowDefinition } from '../../api/types'
import { graphToWorkflow, workflowToGraph } from './graphModel'
import { validateEditorGraph } from './validation'
import WorkflowCanvas from './WorkflowCanvas'

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

function largeWorkflow(): WorkflowDefinition {
  const tasks: TaskDefinition[] = Array.from({ length: 100 }, (_, index) => {
    const id = `TASK-${String(index).padStart(3, '0')}`
    const dependency = index === 0 ? [] : [`TASK-${String(index - 1).padStart(3, '0')}`]
    return {
      id,
      name: `Task ${index}`,
      prompt: `Execute task ${index}`,
      cwd: '.',
      dependencies: dependency,
      execution_mode: 'NEW_THREAD',
      continue_from_task_id: null,
      model: null,
      reasoning_effort: null,
      sandbox: 'workspace_write',
      approval_mode: null,
      timeout_seconds: null,
      retry_policy: { max_attempts: 1 },
    }
  })

  return {
    id: 'large-dag',
    name: 'Large DAG',
    description: 'Deterministic 100-node performance fixture',
    tasks,
    edges: tasks.slice(1).map((task, index) => ({
      source_task_id: tasks[index]!.id,
      target_task_id: task.id,
    })),
  }
}

describe('large DAG UI performance guard', () => {
  it('keeps 100-node mapping and validation bounded and deterministic', () => {
    const workflow = largeWorkflow()
    const graph = workflowToGraph(workflow)

    expect(graph.nodes).toHaveLength(100)
    expect(graph.edges).toHaveLength(99)
    expect(validateEditorGraph(graph)).toEqual([])

    const restored = graphToWorkflow(graph, {
      id: workflow.id,
      name: workflow.name,
      description: workflow.description,
    })
    expect(restored.tasks.map((task) => task.id)).toEqual(workflow.tasks.map((task) => task.id))
    expect(restored.edges).toEqual(workflow.edges)
  })

  it('renders one stable node per task without multiplying render state', () => {
    globalThis.ResizeObserver = ResizeObserverMock
    const graph = workflowToGraph(largeWorkflow())
    render(<WorkflowCanvas graph={graph} />)

    expect(screen.getAllByTestId(/^rf__node-/)).toHaveLength(100)
    expect(screen.getByTestId('rf__minimap')).toBeInTheDocument()
  })
})
