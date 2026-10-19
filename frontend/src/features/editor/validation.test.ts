import { describe, expect, it } from 'vitest'
import { fixtureWorkflow } from '../../test/fixtures'
import { workflowToGraph } from './graphModel'
import { validateEditorGraph } from './validation'

const validGraph = () => workflowToGraph(fixtureWorkflow)
const codes = (graph: ReturnType<typeof validGraph>) => validateEditorGraph(graph).map((issue) => issue.code)

describe('validateEditorGraph', () => {
  it('accepts a valid DAG with consistent dependencies', () => {
    expect(validateEditorGraph(validGraph())).toEqual([])
  })

  it('reports duplicate IDs, blank fields, and unknown targets', () => {
    const graph = validGraph()
    graph.nodes.push(structuredClone(graph.nodes[0]!))
    graph.nodes[0]!.data.task.name = ' '
    graph.nodes[1]!.data.task.prompt = ''
    graph.nodes[1]!.data.task.dependencies = ['missing']
    expect(codes(graph)).toEqual(expect.arrayContaining(['DUPLICATE_TASK_ID', 'REQUIRED_FIELD', 'UNKNOWN_DEPENDENCY_TARGET']))
  })

  it('reports edge/dependency mismatches, duplicate edges, and self edges', () => {
    const graph = validGraph()
    graph.edges.push(structuredClone(graph.edges[0]!))
    graph.edges.push({ id: 'A->A', source: 'A', target: 'A' })
    graph.nodes[1]!.data.task.dependencies = []
    expect(codes(graph)).toEqual(expect.arrayContaining(['DUPLICATE_EDGE', 'SELF_EDGE', 'DEPENDENCY_EDGE_MISMATCH']))
  })

  it('reports cycles', () => {
    const graph = validGraph()
    graph.nodes[0]!.data.task.dependencies = ['B']
    graph.edges.push({ id: 'B->A', source: 'B', target: 'A' })
    expect(codes(graph)).toContain('CYCLE')
  })

  it('reports continuation source violations', () => {
    const graph = validGraph()
    graph.nodes[1]!.data.task.continue_from_task_id = null
    expect(codes(graph)).toContain('CONTINUATION_SOURCE_REQUIRED')
    graph.nodes[1]!.data.task.continue_from_task_id = 'missing'
    expect(codes(graph)).toContain('UNKNOWN_CONTINUATION_SOURCE')
    graph.nodes[1]!.data.task.continue_from_task_id = 'B'
    expect(codes(graph)).toContain('SELF_CONTINUATION_SOURCE')
    graph.nodes[1]!.data.task.execution_mode = 'NEW_THREAD'
    expect(codes(graph)).toContain('NEW_THREAD_CONTINUATION_SOURCE')
  })
})
