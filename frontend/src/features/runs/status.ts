import type { TaskStatus } from '../../api/types'

export type TaskStatusPresentation = {
  label: string
  token: string
}

export const canonicalTaskStatuses: readonly TaskStatus[] = [
  'PENDING', 'READY', 'STARTING', 'RUNNING', 'SUCCESS',
  'FAILED', 'BLOCKED', 'CANCELLED', 'INTERRUPTED', 'NEEDS_ATTENTION',
]

const presentations: Record<TaskStatus, TaskStatusPresentation> = {
  PENDING: { label: 'Pending', token: 'pending' },
  READY: { label: 'Ready', token: 'ready' },
  STARTING: { label: 'Starting', token: 'starting' },
  RUNNING: { label: 'Running', token: 'running' },
  SUCCESS: { label: 'Success', token: 'success' },
  FAILED: { label: 'Failed', token: 'failed' },
  BLOCKED: { label: 'Blocked', token: 'blocked' },
  CANCELLED: { label: 'Cancelled', token: 'cancelled' },
  INTERRUPTED: { label: 'Interrupted', token: 'interrupted' },
  NEEDS_ATTENTION: { label: 'Needs attention', token: 'needs-attention' },
}

export function mapTaskStatus(status: unknown): TaskStatusPresentation {
  if (typeof status === 'string' && status in presentations) {
    return presentations[status as TaskStatus]
  }
  return { label: 'UNKNOWN', token: 'unknown' }
}

export const getTaskStatusPresentation = mapTaskStatus
