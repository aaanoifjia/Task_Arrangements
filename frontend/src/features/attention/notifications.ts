import type { TaskRunView } from '../../api/types'

export type AttentionNotificationTask = Pick<TaskRunView, 'id' | 'task_id' | 'workflow_run_id' | 'status'>

export type NotificationConstructorLike = {
  new (title: string, options?: NotificationOptions): unknown
  permission: NotificationPermission
}

const notifiedTaskRunIds = new Set<string>()

function browserNotification(): NotificationConstructorLike | null {
  if (typeof Notification === 'undefined') return null
  return Notification
}

export function notifyAttentionTasks(
  tasks: readonly AttentionNotificationTask[],
  notificationConstructor: NotificationConstructorLike | null = browserNotification(),
): number {
  if (!notificationConstructor || notificationConstructor.permission !== 'granted') return 0
  let notified = 0
  for (const task of tasks) {
    if (task.status !== 'NEEDS_ATTENTION' || notifiedTaskRunIds.has(task.id)) continue
    new notificationConstructor(`Task needs attention: ${task.task_id}`, {
      body: `Run ${task.workflow_run_id} requires review.`,
      tag: `codex-flow-${task.id}`,
    })
    notifiedTaskRunIds.add(task.id)
    notified += 1
  }
  return notified
}

export function resetAttentionNotificationDedupe(): void {
  notifiedTaskRunIds.clear()
}
