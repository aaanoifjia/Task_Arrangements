import { describe, expect, it } from 'vitest'
import { fixtureWorkflow } from '../../test/fixtures'
import { workflowToGraph } from './graphModel'
import { editorReducer, emptyEditorState } from './editorState'

describe('editor reducer', () => {
  it('loads, selects, updates, and marks saved without mutating prior state', () => {
    const loaded = editorReducer(emptyEditorState, { type: 'load', graph: workflowToGraph(fixtureWorkflow) })
    const updated = editorReducer(loaded, { type: 'update_task', taskId: 'A', changes: { name: 'Changed' } })
    expect(loaded.dirty).toBe(false)
    expect(loaded.graph.nodes[0]?.data.task.name).toBe('First task')
    expect(updated.dirty).toBe(true)
    expect(updated.graph.nodes[0]?.data.task.name).toBe('Changed')
    expect(editorReducer(updated, { type: 'select', taskId: 'A' }).selectedTaskId).toBe('A')
    expect(editorReducer(updated, { type: 'mark_saved' }).dirty).toBe(false)
  })

  it('keeps graph operations deterministic and removes dependent edges', () => {
    const loaded = editorReducer(emptyEditorState, { type: 'load', graph: workflowToGraph(fixtureWorkflow) })
    const connected = editorReducer(loaded, { type: 'connect', source: 'B', target: 'A' })
    const same = editorReducer(connected, { type: 'connect', source: 'B', target: 'A' })
    expect(same.graph.edges).toHaveLength(2)
    expect(same.graph.nodes.find((node) => node.id === 'A')?.data.task.dependencies).toEqual(['B'])
    expect(editorReducer(same, { type: 'connect', source: 'A', target: 'A' })).toBe(same)
    expect(editorReducer(same, { type: 'connect', source: 'missing', target: 'A' })).toBe(same)
    const disconnected = editorReducer(same, { type: 'disconnect', edgeId: 'B->A' })
    expect(disconnected.graph.edges).toHaveLength(1)
    expect(disconnected.graph.nodes.find((node) => node.id === 'A')?.data.task.dependencies).toEqual([])
    expect(editorReducer(disconnected, { type: 'disconnect', edgeId: 'missing' })).toBe(disconnected)
    const removed = editorReducer(same, { type: 'remove_task', taskId: 'A' })
    expect(removed.graph.nodes.map((node) => node.id)).toEqual(['B'])
    expect(removed.graph.edges).toEqual([])
  })
})
