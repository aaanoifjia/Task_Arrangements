import { describe, expect, it } from 'vitest'
import { fixtureWorkflow } from '../../test/fixtures'
import { graphToWorkflow, workflowToGraph } from './graphModel'

describe('editor graph model', () => {
  it('round-trips the workflow without losing task fields', () => {
    const graph = workflowToGraph(fixtureWorkflow)
    const restored = graphToWorkflow(graph, {
      id: fixtureWorkflow.id, name: fixtureWorkflow.name, description: fixtureWorkflow.description,
    })
    expect(restored).toEqual(fixtureWorkflow)
  })
})
