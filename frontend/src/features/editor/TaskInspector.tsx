import type { TaskDefinition } from '../../api/types'
import './TaskInspector.css'

export type TaskInspectorProps = { task: TaskDefinition | null }

function TaskInspector({ task }: TaskInspectorProps) {
  if (!task) {
    return (
      <aside className="task-inspector task-inspector--empty" aria-label="Task inspector">
        <p>Select a task to inspect its configuration.</p>
      </aside>
    )
  }

  return (
    <aside className="task-inspector" aria-label="Task inspector">
      <h2>Task inspector</h2>
      <dl>
        <div>
          <dt>Name</dt>
          <dd>{task.name}</dd>
        </div>
        <div>
          <dt>Task ID</dt>
          <dd>{task.id}</dd>
        </div>
      </dl>
    </aside>
  )
}

export default TaskInspector
