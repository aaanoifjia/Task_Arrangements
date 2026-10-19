import { act, renderHook } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { TaskRunView } from '../../api/types'
import { useRunStream } from './useRunStream'

class FakeWebSocket {
  static instances: FakeWebSocket[] = []
  onmessage: ((event: MessageEvent) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  readonly url: string
  close = vi.fn()

  constructor(url: string) {
    this.url = url
    FakeWebSocket.instances.push(this)
  }
}

const task: TaskRunView = {
  id: 'task-run-a', workflow_run_id: 'run-1', task_id: 'A', status: 'RUNNING',
  thread_id: 'thread-1', turn_id: 'turn-1', created_at: '2026-01-01T00:00:00Z',
}

describe('useRunStream', () => {
  it('applies snapshots and advances the event cursor', () => {
    FakeWebSocket.instances = []
    const { result } = renderHook(() => useRunStream('run-1', { webSocketFactory: FakeWebSocket }))
    const socket = FakeWebSocket.instances[0]!
    act(() => socket.onmessage?.({ data: JSON.stringify({ kind: 'snapshot', payload: { tasks: [task] } }) } as MessageEvent))
    expect(result.current.tasks).toEqual([task])
    expect(result.current.hasSnapshot).toBe(true)
    act(() => socket.onmessage?.({
      data: JSON.stringify({
        kind: 'event',
        payload: { id: 'event-1', event_type: 'TURN_STARTED', payload: {}, created_at: 'now' },
      }),
    } as MessageEvent))
    expect(result.current.latestEventId).toBe('event-1')
    expect(result.current.latestEvent?.event_type).toBe('TURN_STARTED')
  })

  it('closes the old stream on unmount and run change', () => {
    FakeWebSocket.instances = []
    const { rerender, unmount } = renderHook(({ runId }) => useRunStream(runId, { webSocketFactory: FakeWebSocket }), {
      initialProps: { runId: 'run-1' },
    })
    const first = FakeWebSocket.instances[0]!
    rerender({ runId: 'run-2' })
    expect(first.close).toHaveBeenCalledWith(1000, 'run stream cleanup')
    const second = FakeWebSocket.instances[1]!
    unmount()
    expect(second.close).toHaveBeenCalledWith(1000, 'run stream cleanup')
  })
})
