export class MockWebSocket {
  static instances: MockWebSocket[] = []
  readonly url: string
  onmessage: ((event: MessageEvent) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  closed = false

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
  }

  emit(data: unknown): void {
    this.onmessage?.({ data: JSON.stringify(data) } as MessageEvent)
  }

  fail(): void {
    this.onerror?.(new Event('error'))
  }

  close(code = 1000, reason = ''): void {
    this.closed = true
    this.onclose?.({ code, reason } as CloseEvent)
  }
}
