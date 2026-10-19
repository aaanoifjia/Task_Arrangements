import { describe, expect, it } from 'vitest'
import type { TaskDefinition } from '../../api/types'
import { fixtureWorkflow } from '../../test/fixtures'
import { editorReducer, emptyEditorState } from './editorState'
import { workflowToGraph } from './graphModel'
import { renameTaskInGraph } from './fields/TaskBasicsFields'
import { serializeWorkflow } from './serialize'
import { validateEditorGraph } from './validation'

function task(id: string): TaskDefinition {
  return {
    ...structuredClone(fixtureWorkflow.tasks[0]!),
    id,
    name: `Task ${id}`,
    prompt: `Prompt ${id}`,
    dependencies: [],
    execution_mode: 'NEW_THREAD',
    continue_from_task_id: null,
  }
}

describe('Workflow editor regression matrix', () => {
  it('covers fork/join editing, continuation, validation, save serialization, and reload', () => {
    let state = editorReducer(emptyEditorState, {
      type: 'load',
      graph: {
        nodes: ['A', 'B', 'C', 'D'].map((id, index) => ({
          id,
          type: 'task' as const,
          position: { x: index * 100, y: 0 },
          data: { task: task(id) },
        })),
        edges: [],
      },
    })
    for (const [source, target] of [['A', 'B'], ['A', 'C'], ['B', 'D'], ['C', 'D']] as const) {
      state = editorReducer(state, { type: 'connect', source, target })
    }
    expect(validateEditorGraph(state.graph)).toEqual([])
    expect(state.graph.edges).toHaveLength(4)

    const renamedGraph = renameTaskInGraph(state.graph, 'A', 'ROOT')
    expect(renamedGraph.edges.map((edge) => edge.id)).toEqual(['ROOT->B', 'ROOT->C', 'B->D', 'C->D'])
    state = { ...state, graph: renamedGraph }
    state = editorReducer(state, { type: 'update_task', taskId: 'B', changes: { execution_mode: 'CONTINUE_THREAD', continue_from_task_id: 'ROOT' } })
    expect(validateEditorGraph(state.graph)).toEqual([])

    state = editorReducer(state, { type: 'disconnect', edgeId: 'C->D' })
    state = editorReducer(state, { type: 'connect', source: 'C', target: 'D' })
    expect(state.graph.edges).toHaveLength(4)
    state = editorReducer(state, { type: 'remove_task', taskId: 'C' })
    expect(state.graph.nodes.map((node) => node.id)).toEqual(['ROOT', 'B', 'D'])
    expect(state.graph.edges.map((edge) => edge.id)).toEqual(['ROOT->B', 'B->D'])
    expect(validateEditorGraph(state.graph)).toEqual([])

    const metadata = { id: 'workflow-matrix', name: 'Matrix', description: null }
    const payload = serializeWorkflow(state.graph, metadata)
    const reloaded = workflowToGraph(payload)
    expect(serializeWorkflow(reloaded, metadata)).toEqual(payload)

    const cycle = editorReducer(state, { type: 'connect', source: 'D', target: 'ROOT' })
    expect(validateEditorGraph(cycle.graph).map((issue) => issue.code)).toContain('CYCLE')
  })
})
