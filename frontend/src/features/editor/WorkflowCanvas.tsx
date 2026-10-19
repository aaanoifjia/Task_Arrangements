import { useMemo } from 'react'
import { Background, Controls, ReactFlow, type Connection, type Edge, type Node } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import type { EditorGraph } from './graphModel'
import TaskNode from './TaskNode'
import type { TaskNodeData } from './TaskNode'
import './WorkflowCanvas.css'

type WorkflowCanvasProps = {
  graph: EditorGraph
  selectedTaskId?: string | null
  onSelectTask?: (taskId: string) => void
  onConnect?: (source: string, target: string) => void
  onDisconnect?: (edgeId: string) => void
}

function WorkflowCanvas({ graph, selectedTaskId, onSelectTask, onConnect, onDisconnect }: WorkflowCanvasProps) {
  const nodes = useMemo<Node[]>(() => graph.nodes.map((node) => ({
    id: node.id,
    type: 'task',
    position: node.position,
    data: { task: node.data.task } satisfies TaskNodeData,
    selected: node.id === selectedTaskId,
  })), [graph.nodes, selectedTaskId])
  const edges = useMemo<Edge[]>(() => graph.edges.map((edge) => ({
    id: edge.id, source: edge.source, target: edge.target,
  })), [graph.edges])

  return (
    <div className="workflow-canvas" data-testid="workflow-canvas">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={{ task: TaskNode }}
        fitView
        onNodeClick={(_, node) => onSelectTask?.(node.id)}
        onConnect={(connection: Connection) => {
          if (connection.source && connection.target) onConnect?.(connection.source, connection.target)
        }}
        onEdgesDelete={(deletedEdges) => deletedEdges.forEach((edge) => onDisconnect?.(edge.id))}
        aria-label="Workflow graph canvas"
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  )
}

export default WorkflowCanvas
