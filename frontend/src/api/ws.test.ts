import { describe, expect, it, vi } from 'vitest'
import { buildRunWebSocketUrl, RunWebSocketClient } from './ws'

class FakeWebSocket {
  static instance: FakeWebSocket | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  readonly url: string
  close = vi.fn()

  constructor(url: string) {
    this.url = url
    FakeWebSocket.instance = this
  }
}

describe('run WebSocket client', () => {
  it('builds a cursor URL and parses stream messages', () => {
    expect(buildRunWebSocketUrl('run id', 'event-1')).toMatch(/^ws:\/\/localhost(?::\d+)?\/ws\/runs\/run%20id\?after=event-1$/)
    const onMessage = vi.fn()
    const client = new RunWebSocketClient('run id', { after: 'event-1', onMessage, webSocketFactory: FakeWebSocket })
    client.connect()
    expect(FakeWebSocket.instance?.url).toContain('/ws/runs/run%20id?after=event-1')
    FakeWebSocket.instance?.onmessage?.({ data: JSON.stringify({ kind: 'snapshot', payload: { tasks: [] } }) } as MessageEvent)
    expect(onMessage).toHaveBeenCalledWith({ kind: 'snapshot', payload: { tasks: [] } })
  })

  it('uses the desktop loopback URL and encodes the bearer token', () => {
    expect(buildRunWebSocketUrl('run/1', 'cursor/2', {
      baseUrl: 'http://127.0.0.1:43127',
      token: 'token with/slash',
    })).toBe('ws://127.0.0.1:43127/ws/runs/run%2F1?after=cursor%2F2&token=token+with%2Fslash')
  })

  it('closes explicitly and does not mutate application state', () => {
    const client = new RunWebSocketClient('run', { webSocketFactory: FakeWebSocket })
    client.connect()
    client.close(1000, 'done')
    expect(FakeWebSocket.instance?.close).toHaveBeenCalledWith(1000, 'done')
  })
})
