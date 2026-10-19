import { useEffect, useRef, useState } from 'react'
import type { EventView, TaskRunView, StreamMessage } from '../../api/types'
import { RunWebSocketClient, type WebSocketFactory } from '../../api/ws'

export type UseRunStreamOptions = { webSocketFactory?: WebSocketFactory; terminal?: boolean }

export type RunStreamState = {
  tasks: TaskRunView[]
  hasSnapshot: boolean
  latestEvent: EventView | null
  latestEventId: string | null
  connected: boolean
}

const emptyState: RunStreamState = {
  tasks: [], hasSnapshot: false, latestEvent: null, latestEventId: null, connected: false,
}

const terminalTaskStatuses = new Set(['SUCCESS', 'FAILED', 'BLOCKED', 'CANCELLED', 'INTERRUPTED', 'NEEDS_ATTENTION'])

function isTerminalSnapshot(tasks: TaskRunView[]): boolean {
  return tasks.length > 0 && tasks.every((task) => terminalTaskStatuses.has(task.status))
}

function applyMessage(message: StreamMessage, setState: (update: (current: RunStreamState) => RunStreamState) => void) {
  if (message.kind === 'snapshot') {
    setState((current) => ({ ...current, tasks: message.payload.tasks, hasSnapshot: true }))
    return
  }
  setState((current) => ({
    ...current,
    latestEvent: message.payload,
    latestEventId: message.payload.id,
  }))
}

export function useRunStream(runId: string | null | undefined, options: UseRunStreamOptions = {}): RunStreamState {
  const [state, setState] = useState<RunStreamState>(emptyState)
  const { terminal = false, webSocketFactory } = options
  const eventCursor = useRef<string | null>(null)
  const seenEventIds = useRef<Set<string>>(new Set())

  useEffect(() => {
    if (!runId || terminal) {
      setState(emptyState)
      return undefined
    }

    let active = true
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null
    let reconnectAttempt = 0
    let client: RunWebSocketClient | null = null
    let terminalSnapshotObserved = false
    const reconnectDelays = [250, 500, 1000, 2000, 4000] as const
    setState(emptyState)

    const connect = () => {
      if (!active) return
      client = new RunWebSocketClient(runId, {
        after: eventCursor.current ?? undefined,
        webSocketFactory,
        onMessage: (message) => {
          if (!active) return
          if (message.kind === 'snapshot' && isTerminalSnapshot(message.payload.tasks)) {
            terminalSnapshotObserved = true
          }
          if (message.kind === 'event') {
            if (seenEventIds.current.has(message.payload.id)) return
            seenEventIds.current.add(message.payload.id)
            eventCursor.current = message.payload.id
          }
          applyMessage(message, setState)
        },
        onClose: () => {
          if (!active) return
          setState((current) => ({ ...current, connected: false }))
          if (terminalSnapshotObserved) return
          const delay = reconnectDelays[Math.min(reconnectAttempt, reconnectDelays.length - 1)]
          reconnectAttempt += 1
          reconnectTimer = setTimeout(connect, delay)
        },
      })
      client.connect()
      setState((current) => ({ ...current, connected: true }))
    }

    eventCursor.current = null
    seenEventIds.current = new Set()
    connect()
    return () => {
      active = false
      if (reconnectTimer) clearTimeout(reconnectTimer)
      client?.close(1000, 'run stream cleanup')
    }
  }, [runId, terminal, webSocketFactory])

  return state
}
