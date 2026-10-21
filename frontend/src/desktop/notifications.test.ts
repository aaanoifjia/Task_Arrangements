import { describe, expect, it, vi } from 'vitest'
import { notifyDesktopAttention, type DesktopNotificationApi } from './notifications'

const task = {
  id: 'task-run-1',
  task_id: 'review',
  workflow_run_id: 'run-1',
  status: 'NEEDS_ATTENTION' as const,
}

function api(overrides: Partial<DesktopNotificationApi> = {}): DesktopNotificationApi {
  return {
    isPermissionGranted: vi.fn().mockResolvedValue(true),
    requestPermission: vi.fn().mockResolvedValue('granted'),
    sendNotification: vi.fn().mockResolvedValue(undefined),
    ...overrides,
  }
}

describe('desktop notifications', () => {
  it('sends a native attention notification when permission is granted', async () => {
    const notificationApi = api()

    await expect(notifyDesktopAttention(task, notificationApi)).resolves.toBe(true)
    expect(notificationApi.sendNotification).toHaveBeenCalledWith({
      title: 'Task needs attention: review',
      body: 'Run run-1 requires review.',
      tag: 'codex-flow-task-run-1',
    })
  })

  it('requests permission and stays quiet when permission is denied', async () => {
    const notificationApi = api({
      isPermissionGranted: vi.fn().mockResolvedValue(false),
      requestPermission: vi.fn().mockResolvedValue('denied'),
    })

    await expect(notifyDesktopAttention(task, notificationApi)).resolves.toBe(false)
    expect(notificationApi.sendNotification).not.toHaveBeenCalled()
  })
})
