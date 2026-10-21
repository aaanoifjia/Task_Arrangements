import type { StreamMessage } from './types'

type WebSocketLike = Pick<WebSocket, 'onmessage' | 'onclose' | 'onerror' | 'close'>
export type WebSocketRuntime = {
  baseUrl: string
  token: string
}
export type WebSocketFactory = new (url: string) => WebSocketLike
export type RunWebSocketOptions = {
  after?: string
  runtime?: WebSocketRuntime
  onMessage?: (message: StreamMessage) => void
  onClose?: (event: CloseEvent) => void
  onError?: (event: Event) => void
  webSocketFactory?: WebSocketFactory
}

export function buildRunWebSocketUrl(runId: string, after?: string, runtime?: WebSocketRuntime): string {
  const origin = runtime?.baseUrl
    ?? (typeof window === 'undefined' ? 'http://localhost' : window.location.origin)
  const url = new URL(`/ws/runs/${encodeURIComponent(runId)}`, origin)
  if (after) url.searchParams.set('after', after)
  if (runtime?.token) url.searchParams.set('token', runtime.token)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  return url.toString()
}

function isStreamMessage(value: unknown): value is StreamMessage {
  return typeof value === 'object' && value !== null
    && ((value as { kind?: unknown }).kind === 'event' || (value as { kind?: unknown }).kind === 'snapshot')
}

export class RunWebSocketClient {
  private socket: WebSocketLike | null = null
  private readonly options: RunWebSocketOptions

  constructor(private readonly runId: string, options: RunWebSocketOptions = {}) {
    this.options = options
  }

  connect(): void {
    if (this.socket) return
    const factory = this.options.webSocketFactory ?? WebSocket
    const socket = new factory(buildRunWebSocketUrl(this.runId, this.options.after, this.options.runtime))
    this.socket = socket
    socket.onmessage = (event) => {
      try {
        const message: unknown = JSON.parse(String(event.data))
        if (isStreamMessage(message)) this.options.onMessage?.(message)
      } catch {
        // Ignore malformed transport messages; state is owned by the server.
      }
    }
    socket.onclose = (event) => {
      this.socket = null
      this.options.onClose?.(event)
    }
    socket.onerror = (event) => this.options.onError?.(event)
  }

  close(code?: number, reason?: string): void {
    this.socket?.close(code, reason)
    this.socket = null
  }
}
