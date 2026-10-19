import type { TaskStatus } from '../../api/types'
import './TaskStateNotice.css'

const messages: Partial<Record<TaskStatus, string>> = {
  FAILED: 'Task failed during execution. Review the event log for durable execution details.',
  INTERRUPTED: 'Task execution was interrupted before completion.',
  BLOCKED: 'Task is blocked because a dependency or recovery condition has not released it.',
  NEEDS_ATTENTION: 'Task requires attention because execution did not reach a confirmed terminal success.',
}

export type TaskStateNoticeProps = { status: unknown }

function TaskStateNotice({ status }: TaskStateNoticeProps) {
  if (typeof status !== 'string' || !(status in messages)) return null
  return (
    <aside className={`task-state-notice task-state-notice--${status.toLowerCase()}`} aria-live="polite">
      <strong>{status}</strong>
      <p>{messages[status as TaskStatus]}</p>
    </aside>
  )
}

export default TaskStateNotice
