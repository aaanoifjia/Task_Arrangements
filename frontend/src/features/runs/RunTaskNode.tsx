import { Handle, Position } from '@xyflow/react'
import { mapTaskStatus } from './status'
import './RunTaskNode.css'

export type RunTaskNodeData = {
  taskId: string
  taskName: string
  status: unknown
  threadId?: string | null
  turnId?: string | null
}

export type RunTaskNodeProps = { data: RunTaskNodeData }

function RunTaskNode({ data }: RunTaskNodeProps) {
  const presentation = mapTaskStatus(data.status)
  return (
    <article
      className={`run-task-node run-task-node--${presentation.token}`}
      aria-label={`Task ${data.taskName}`}
      data-status={presentation.token}
    >
      <Handle type="target" position={Position.Top} isConnectable={false} aria-label={`Run dependency input for ${data.taskId}`} />
      <div className="run-task-node__name">{data.taskName}</div>
      <div className="run-task-node__id">{data.taskId}</div>
      <div className="run-task-node__status" role="status">{presentation.label}</div>
      {data.threadId && <div className="run-task-node__reference">Thread: {data.threadId}</div>}
      {data.turnId && <div className="run-task-node__reference">Turn: {data.turnId}</div>}
      <Handle type="source" position={Position.Bottom} isConnectable={false} aria-label={`Run dependency output for ${data.taskId}`} />
    </article>
  )
}

export default RunTaskNode
