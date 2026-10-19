import type { WorkflowDefinition } from '../../api/types'
import type { EditorGraph } from './graphModel'

export type WorkflowMetadata = Pick<WorkflowDefinition, 'id' | 'name' | 'description'>

function compareEdges(left: { source: string; target: string }, right: { source: string; target: string }): number {
  if (left.source !== right.source) return left.source < right.source ? -1 : 1
  if (left.target !== right.target) return left.target < right.target ? -1 : 1
  return 0
}

export function serializeWorkflow(graph: EditorGraph, metadata: WorkflowMetadata): WorkflowDefinition {
  const sortedEdges = [...graph.edges].sort(compareEdges)
  const dependencies = new Map<string, string[]>()
  for (const edge of sortedEdges) {
    const taskDependencies = dependencies.get(edge.target) ?? []
    if (!taskDependencies.includes(edge.source)) taskDependencies.push(edge.source)
    dependencies.set(edge.target, taskDependencies)
  }
  return {
    ...metadata,
    tasks: graph.nodes.map((node) => ({
      ...structuredClone(node.data.task),
      id: node.id,
      dependencies: [...(dependencies.get(node.id) ?? [])],
    })),
    edges: sortedEdges.map((edge) => ({ source_task_id: edge.source, target_task_id: edge.target })),
  }
}
