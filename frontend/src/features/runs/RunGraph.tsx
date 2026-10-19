import { useMemo } from 'react'
import { Background, Controls, MiniMap, ReactFlow, type Edge, type Node } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import type { TaskRunView } from '../../api/types'
import './RunGraph.css'

type SnapshotTask = { id: string; name: string }
type SnapshotEdge = { source_task_id: string; target_task_id: string }

export type RunGraphProps = {
  snapshot: Record<string, unknown>
  taskRuns: TaskRunView[]
}

function readSnapshotTasks(snapshot: Record<string, unknown>): SnapshotTask[] {
  if (!Array.isArray(snapshot.tasks)) return []
  return snapshot.tasks.flatMap((value) => {
    if (typeof value !== 'object' || value === null) return []
    const task = value as { id?: unknown; name?: unknown }
    if (typeof task.id !== 'string') return []
    return [{ id: task.id, name: typeof task.name === 'string' ? task.name : task.id }]
  })
}

function readSnapshotEdges(snapshot: Record<string, unknown>, knownIds: Set<string>): SnapshotEdge[] {
  if (!Array.isArray(snapshot.edges)) return []
  return snapshot.edges.flatMap((value) => {
    if (typeof value !== 'object' || value === null) return []
    const edge = value as { source_task_id?: unknown; target_task_id?: unknown }
    if (typeof edge.source_task_id !== 'string' || typeof edge.target_task_id !== 'string') return []
    if (!knownIds.has(edge.source_task_id) || !knownIds.has(edge.target_task_id)) return []
    return [{ source_task_id: edge.source_task_id, target_task_id: edge.target_task_id }]
  })
}

function RunGraph({ snapshot, taskRuns }: RunGraphProps) {
  const taskDefinitions = useMemo(() => readSnapshotTasks(snapshot), [snapshot])
  const taskStatuses = useMemo(() => new Map(taskRuns.map((task) => [task.task_id, task.status])), [taskRuns])
  const nodes = useMemo<Node<{ label: string }>[]>(() => taskDefinitions.map((task, index) => ({
    id: task.id,
    position: { x: (index % 3) * 280, y: Math.floor(index / 3) * 180 },
    data: { label: `${task.name} — ${taskStatuses.get(task.id) ?? 'PENDING'}` },
  })), [taskDefinitions, taskStatuses])
  const edges = useMemo<Edge[]>(() => {
    const knownIds = new Set(taskDefinitions.map((task) => task.id))
    return readSnapshotEdges(snapshot, knownIds).map((edge) => ({
      id: `${edge.source_task_id}->${edge.target_task_id}`,
      source: edge.source_task_id,
      target: edge.target_task_id,
    }))
  }, [snapshot, taskDefinitions])

  return (
    <div className="run-graph" data-testid="run-graph" data-read-only="true" aria-label="Read-only run snapshot graph">
      {nodes.length === 0
        ? <p>No snapshot graph available.</p>
        : <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          nodesDraggable={false}
          nodesConnectable={false}
          edgesReconnectable={false}
          elementsSelectable={false}
          aria-label="Read-only run graph canvas"
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>}
    </div>
  )
}

export default RunGraph
