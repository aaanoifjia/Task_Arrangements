import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fixtureTaskRun } from '../../test/fixtures'
import { notifyAttentionTasks, resetAttentionNotificationDedupe, type NotificationConstructorLike } from './notifications'

class FakeNotification {
  static permission: NotificationPermission = 'granted'
  static requestPermission = vi.fn()
  static instances: FakeNotification[] = []

  constructor(readonly title: string, readonly options?: NotificationOptions) {
    FakeNotification.instances.push(this)
  }
}

const notificationConstructor = FakeNotification as unknown as NotificationConstructorLike

describe('attention notifications', () => {
  beforeEach(() => {
    resetAttentionNotificationDedupe()
    FakeNotification.permission = 'granted'
    FakeNotification.requestPermission.mockReset()
    FakeNotification.instances = []
  })

  it('notifies once per newly observed attention TaskRun when permission is granted', () => {
    const task = { ...fixtureTaskRun, status: 'NEEDS_ATTENTION' as const }
    expect(notifyAttentionTasks([task], notificationConstructor)).toBe(1)
    expect(notifyAttentionTasks([task], notificationConstructor)).toBe(0)
    expect(FakeNotification.instances).toHaveLength(1)
    expect(FakeNotification.instances[0]?.title).toBe('Task needs attention: A')
    expect(FakeNotification.instances[0]?.options).toMatchObject({ tag: 'codex-flow-task-run-a' })
    expect(FakeNotification.requestPermission).not.toHaveBeenCalled()
  })

  it.each<NotificationPermission>(['denied', 'default'])('does not notify or request permission when permission is %s', (permission) => {
    FakeNotification.permission = permission
    const task = { ...fixtureTaskRun, status: 'NEEDS_ATTENTION' as const }
    expect(notifyAttentionTasks([task], notificationConstructor)).toBe(0)
    expect(FakeNotification.instances).toHaveLength(0)
    expect(FakeNotification.requestPermission).not.toHaveBeenCalled()
  })

  it('deduplicates by TaskRun id while notifying distinct attention tasks', () => {
    const first = { ...fixtureTaskRun, status: 'NEEDS_ATTENTION' as const }
    const second = { ...fixtureTaskRun, id: 'task-run-b', task_id: 'B', status: 'NEEDS_ATTENTION' as const }
    expect(notifyAttentionTasks([first, second], notificationConstructor)).toBe(2)
    expect(notifyAttentionTasks([{ ...first, task_id: 'A-renamed' }, second], notificationConstructor)).toBe(0)
    expect(FakeNotification.instances).toHaveLength(2)
  })
})
