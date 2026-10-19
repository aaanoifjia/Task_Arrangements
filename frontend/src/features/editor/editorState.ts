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

export function createDefaultTask(graph: EditorGraph): { task: TaskDefinition; position: { x: number; y: number } } {
  const existingIds = new Set(graph.nodes.map((node) => node.id))
  let sequence = 1
  let id = `new-task-${sequence}`
  while (existingIds.has(id)) {
    sequence += 1
    id = `new-task-${sequence}`
  }
  const index = graph.nodes.length
  return {
    task: {
      id,
      name: 'New task',
      prompt: '',
      cwd: '.',
      dependencies: [],
      execution_mode: 'NEW_THREAD',
      continue_from_task_id: null,
      model: null,
      reasoning_effort: null,
      sandbox: 'workspace_write',
      approval_mode: null,
      timeout_seconds: null,
      retry_policy: { max_attempts: 1 },
    },
    position: { x: (index % 3) * 280, y: Math.floor(index / 3) * 180 },
  }
}

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
      if (action.source === action.target) return state
      if (!state.graph.nodes.some((node) => node.id === action.source) || !state.graph.nodes.some((node) => node.id === action.target)) return state
      const edgeId = `${action.source}->${action.target}`
      if (state.graph.edges.some((edge) => edge.id === edgeId)) return state
      const edge: EditorEdge = { id: edgeId, source: action.source, target: action.target }
      const nodes = state.graph.nodes.map((node) => node.id === action.target
        ? { ...node, data: { task: { ...node.data.task, dependencies: [...new Set([...node.data.task.dependencies, action.source])] } } }
        : node)
      return { ...state, graph: { nodes, edges: [...state.graph.edges, edge] }, dirty: true }
    }
    case 'disconnect': {
      const removedEdge = state.graph.edges.find((edge) => edge.id === action.edgeId)
      if (!removedEdge) return state
      const nodes = state.graph.nodes.map((node) => node.id === removedEdge.target
        ? { ...node, data: { task: { ...node.data.task, dependencies: node.data.task.dependencies.filter((dependency) => dependency !== removedEdge.source) } } }
        : node)
      return { ...state, graph: { nodes, edges: state.graph.edges.filter((edge) => edge.id !== action.edgeId) }, dirty: true }
    }
    case 'select':
      return { ...state, selectedTaskId: action.taskId }
    case 'mark_saved':
      return { ...state, dirty: false }
  }
}
