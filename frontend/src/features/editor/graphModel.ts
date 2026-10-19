import type { Edge, TaskDefinition, WorkflowDefinition } from '../../api/types'

export type GraphPosition = { x: number; y: number }
export type EditorNode = {
  id: string
  type: 'task'
  position: GraphPosition
  data: { task: TaskDefinition }
}
export type EditorEdge = { id: string; source: string; target: string }
export type EditorGraph = { nodes: EditorNode[]; edges: EditorEdge[] }

export function workflowToGraph(workflow: WorkflowDefinition): EditorGraph {
  return {
    nodes: workflow.tasks.map((task, index) => ({
      id: task.id,
      type: 'task',
      position: { x: (index % 3) * 280, y: Math.floor(index / 3) * 180 },
      data: { task: structuredClone(task) },
    })),
    edges: workflow.edges.map((edge) => ({
      id: `${edge.source_task_id}->${edge.target_task_id}`,
      source: edge.source_task_id,
      target: edge.target_task_id,
    })),
  }
}

export function graphToWorkflow(graph: EditorGraph, metadata: Omit<WorkflowDefinition, 'tasks' | 'edges'>): WorkflowDefinition {
  const dependencies = new Map<string, string[]>()
  for (const edge of graph.edges) dependencies.set(edge.target, [...(dependencies.get(edge.target) ?? []), edge.source])
  const edges: Edge[] = graph.edges.map(({ source, target }) => ({ source_task_id: source, target_task_id: target }))
  const tasks = graph.nodes.map((node) => ({
    ...structuredClone(node.data.task),
    id: node.id,
    dependencies: dependencies.get(node.id) ?? [],
  }))
  return { ...metadata, tasks, edges }
}
