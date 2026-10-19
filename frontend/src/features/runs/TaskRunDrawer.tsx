import type { TaskRunView } from '../../api/types'
import type { RunApi } from './api'
import AttemptHistory from './AttemptHistory'
import OpenInCodex from './OpenInCodex'
import './TaskRunDrawer.css'

export type TaskRunDrawerProps = {
  task: TaskRunView | null
  onClose: () => void
  attemptApi?: Pick<RunApi, 'attempts'>
}

function optionalValue(value: string | null): string {
  return value ?? 'Not available'
}

function TaskRunDrawer({ task, onClose, attemptApi }: TaskRunDrawerProps) {
  if (!task) return null
  return (
    <aside className="task-run-drawer" aria-labelledby="task-run-drawer-heading" data-testid="task-run-drawer">
      <div className="task-run-drawer__header">
        <h2 id="task-run-drawer-heading">Task {task.task_id}</h2>
        <button type="button" onClick={onClose} aria-label="Close task details">Close</button>
      </div>
      <dl>
        <div><dt>Task ID</dt><dd>{task.task_id}</dd></div>
        <div><dt>Status</dt><dd>{task.status}</dd></div>
        <div><dt>Thread ID</dt><dd>{optionalValue(task.thread_id)}</dd></div>
        <div><dt>Turn ID</dt><dd>{optionalValue(task.turn_id)}</dd></div>
        <div><dt>Created</dt><dd><time dateTime={task.created_at}>{task.created_at}</time></dd></div>
      </dl>
      <p><OpenInCodex threadId={task.thread_id} /></p>
      <AttemptHistory runId={task.workflow_run_id} taskId={task.task_id} api={attemptApi} />
    </aside>
  )
}

export default TaskRunDrawer
