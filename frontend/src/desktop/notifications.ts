import { isPermissionGranted, requestPermission, sendNotification } from '@tauri-apps/plugin-notification'
import type { AttentionNotificationTask } from '../features/attention/notifications'

export type DesktopNotificationApi = {
  isPermissionGranted: () => Promise<boolean>
  requestPermission: () => Promise<string>
  sendNotification: (options: { title: string; body: string; tag: string }) => Promise<void> | void
}

const defaultNotificationApi: DesktopNotificationApi = {
  isPermissionGranted,
  requestPermission,
  sendNotification,
}

export async function notifyDesktopAttention(
  task: AttentionNotificationTask,
  api: DesktopNotificationApi = defaultNotificationApi,
): Promise<boolean> {
  let granted = await api.isPermissionGranted()
  if (!granted) granted = (await api.requestPermission()) === 'granted'
  if (!granted) return false

  await api.sendNotification({
    title: `Task needs attention: ${task.task_id}`,
    body: `Run ${task.workflow_run_id} requires review.`,
    tag: `codex-flow-${task.id}`,
  })
  return true
}
