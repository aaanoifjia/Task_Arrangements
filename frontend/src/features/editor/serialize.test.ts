import { describe, expect, it } from 'vitest'
import { fixtureWorkflow } from '../../test/fixtures'
import { workflowToGraph } from './graphModel'
import { serializeWorkflow } from './serialize'

describe('serializeWorkflow', () => {
  it('matches the golden WorkflowDefinition payload', () => {
    const graph = workflowToGraph(fixtureWorkflow)
    expect(serializeWorkflow(graph, {
      id: fixtureWorkflow.id,
      name: fixtureWorkflow.name,
      description: fixtureWorkflow.description,
    })).toEqual(fixtureWorkflow)
  })

  it('preserves node order and sorts edges while deriving dependencies once', () => {
    const graph = workflowToGraph(fixtureWorkflow)
    graph.nodes.reverse()
    graph.edges.push({ id: 'B->A', source: 'B', target: 'A' })
    const result = serializeWorkflow(graph, { id: 'workflow-2', name: 'Changed', description: null })
    expect(result.tasks.map((task) => task.id)).toEqual(['B', 'A'])
    expect(result.edges).toEqual([
      { source_task_id: 'A', target_task_id: 'B' },
      { source_task_id: 'B', target_task_id: 'A' },
    ])
    expect(result.tasks.find((task) => task.id === 'A')?.dependencies).toEqual(['B'])
    expect(result.tasks.find((task) => task.id === 'B')?.dependencies).toEqual(['A'])
  })
})
