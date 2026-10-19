import { Handle, Position } from '@xyflow/react'
import type { TaskDefinition } from '../../api/types'
import './TaskNode.css'

export type TaskNodeData = { task: TaskDefinition }
export type TaskNodeProps = { data: TaskNodeData; selected?: boolean }

function TaskNode({ data, selected = false }: TaskNodeProps) {
  const { task } = data
  return (
    <article className={`task-node${selected ? ' task-node--selected' : ''}`} aria-label={`Task ${task.name}`}>
      <Handle type="target" position={Position.Top} aria-label={`Dependency input for ${task.id}`} />
      <div className="task-node__name">{task.name}</div>
      <div className="task-node__id">{task.id}</div>
      <div className="task-node__meta">{task.execution_mode}</div>
      <div className="task-node__cwd">{task.cwd}</div>
      <Handle type="source" position={Position.Bottom} aria-label={`Dependency output for ${task.id}`} />
    </article>
  )
}

export default TaskNode
