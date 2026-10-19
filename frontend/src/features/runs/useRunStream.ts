import { useEffect, useState } from 'react'
import type { EventView, TaskRunView, StreamMessage } from '../../api/types'
import { RunWebSocketClient, type WebSocketFactory } from '../../api/ws'

export type UseRunStreamOptions = { webSocketFactory?: WebSocketFactory }

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
  const { webSocketFactory } = options

  useEffect(() => {
    if (!runId) {
      setState(emptyState)
      return undefined
    }

    let active = true
    setState(emptyState)
    const client = new RunWebSocketClient(runId, {
      webSocketFactory,
      onMessage: (message) => {
        if (active) applyMessage(message, setState)
      },
      onClose: () => {
        if (active) setState((current) => ({ ...current, connected: false }))
      },
    })
    client.connect()
    setState((current) => ({ ...current, connected: true }))
    return () => {
      active = false
      client.close(1000, 'run stream cleanup')
    }
  }, [runId, webSocketFactory])

  return state
}
