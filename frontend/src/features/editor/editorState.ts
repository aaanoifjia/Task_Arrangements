import type { TaskDefinition } from '../../api/types'
import type { EditorEdge, EditorGraph, EditorNode } from './graphModel'

export type EditorState = {
  graph: EditorGraph
  selectedTaskId: string | null
  dirty: boolean
}

export type EditorAction =
  | { type: 'load'; graph: EditorGraph }
  | { type: 'add_task'; task: TaskDefinition; position: { x: number; y: number } }
  | { type: 'remove_task'; taskId: string }
  | { type: 'update_task'; taskId: string; changes: Partial<TaskDefinition> }
  | { type: 'connect'; source: string; target: string }
  | { type: 'disconnect'; edgeId: string }
  | { type: 'select'; taskId: string | null }
  | { type: 'mark_saved' }

export const emptyEditorState: EditorState = { graph: { nodes: [], edges: [] }, selectedTaskId: null, dirty: false }

function nodeFor(task: TaskDefinition, position: { x: number; y: number }): EditorNode {
  return { id: task.id, type: 'task', position: { ...position }, data: { task: structuredClone(task) } }
}

export function editorReducer(state: EditorState, action: EditorAction): EditorState {
  switch (action.type) {
    case 'load':
      return { graph: structuredClone(action.graph), selectedTaskId: null, dirty: false }
    case 'add_task':
      return { ...state, graph: { ...state.graph, nodes: [...state.graph.nodes, nodeFor(action.task, action.position)] }, dirty: true }
    case 'remove_task':
      return {
        ...state,
        graph: {
          nodes: state.graph.nodes.filter((node) => node.id !== action.taskId),
          edges: state.graph.edges.filter((edge) => edge.source !== action.taskId && edge.target !== action.taskId),
        },
        selectedTaskId: state.selectedTaskId === action.taskId ? null : state.selectedTaskId,
        dirty: true,
      }
    case 'update_task':
      return {
        ...state,
        graph: {
          ...state.graph,
          nodes: state.graph.nodes.map((node) => node.id === action.taskId
            ? { ...node, data: { task: { ...node.data.task, ...action.changes } } }
            : node),
        },
        dirty: true,
      }
    case 'connect': {
      const edgeId = `${action.source}->${action.target}`
      if (state.graph.edges.some((edge) => edge.id === edgeId)) return state
      const edge: EditorEdge = { id: edgeId, source: action.source, target: action.target }
      return { ...state, graph: { ...state.graph, edges: [...state.graph.edges, edge] }, dirty: true }
    }
    case 'disconnect':
      return { ...state, graph: { ...state.graph, edges: state.graph.edges.filter((edge) => edge.id !== action.edgeId) }, dirty: true }
    case 'select':
      return { ...state, selectedTaskId: action.taskId }
    case 'mark_saved':
      return { ...state, dirty: false }
  }
}
