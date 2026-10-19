import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
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
  afterEach(() => {
    vi.useRealTimers()
  })

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

  it('reconnects from the last event cursor after an unexpected close', () => {
    vi.useFakeTimers()
    FakeWebSocket.instances = []
    renderHook(() => useRunStream('run-1', { webSocketFactory: FakeWebSocket }))
    const first = FakeWebSocket.instances[0]!
    act(() => first.onmessage?.({
      data: JSON.stringify({ kind: 'event', payload: { id: 'event-1', event_type: 'TURN_STARTED', payload: {}, created_at: 'now' } }),
    } as MessageEvent))
    act(() => first.onclose?.({ code: 1006 } as CloseEvent))
    expect(FakeWebSocket.instances).toHaveLength(1)
    act(() => vi.advanceTimersByTime(249))
    expect(FakeWebSocket.instances).toHaveLength(1)
    act(() => vi.advanceTimersByTime(1))
    expect(FakeWebSocket.instances).toHaveLength(2)
    expect(FakeWebSocket.instances[1]!.url).toContain('after=event-1')
  })

  it('does not publish a duplicate event id', () => {
    FakeWebSocket.instances = []
    const { result } = renderHook(() => useRunStream('run-1', { webSocketFactory: FakeWebSocket }))
    const socket = FakeWebSocket.instances[0]!
    const message = { data: JSON.stringify({ kind: 'event', payload: { id: 'event-1', event_type: 'TURN_STARTED', payload: {}, created_at: 'now' } }) } as MessageEvent
    act(() => socket.onmessage?.(message))
    const firstEvent = result.current.latestEvent
    act(() => socket.onmessage?.(message))
    expect(result.current.latestEvent).toBe(firstEvent)
  })

  it('does not connect or reconnect for a terminal run', () => {
    vi.useFakeTimers()
    FakeWebSocket.instances = []
    renderHook(() => useRunStream('run-1', { terminal: true, webSocketFactory: FakeWebSocket }))
    expect(FakeWebSocket.instances).toHaveLength(0)
    act(() => vi.advanceTimersByTime(5000))
    expect(FakeWebSocket.instances).toHaveLength(0)
  })

  it('stops after a terminal task snapshot even when the socket closes normally', () => {
    vi.useFakeTimers()
    FakeWebSocket.instances = []
    renderHook(() => useRunStream('run-1', { webSocketFactory: FakeWebSocket }))
    const socket = FakeWebSocket.instances[0]!
    act(() => socket.onmessage?.({
      data: JSON.stringify({ kind: 'snapshot', payload: { tasks: [{ ...task, status: 'SUCCESS' }] } }),
    } as MessageEvent))
    act(() => socket.onclose?.({ code: 1000 } as CloseEvent))
    act(() => vi.advanceTimersByTime(5000))
    expect(FakeWebSocket.instances).toHaveLength(1)
  })
})
