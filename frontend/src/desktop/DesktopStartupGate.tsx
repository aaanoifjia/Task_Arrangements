import { useEffect, useState, type ReactNode } from 'react'
import { isTauriEnvironment, loadRuntimeState, type DesktopRuntimeState } from './runtime'
import './DesktopStartupGate.css'

type StartupState = 'loading' | 'ready' | 'failed'
const MAX_MANUAL_RETRIES = 3

const defaultLoadState = () => loadRuntimeState()

export type DesktopStartupGateProps = {
  children: ReactNode
  loadState?: () => Promise<DesktopRuntimeState | null>
}

export default function DesktopStartupGate({ children, loadState = defaultLoadState }: DesktopStartupGateProps) {
  const isBrowser = loadState === defaultLoadState && !isTauriEnvironment()
  const [status, setStatus] = useState<StartupState>(isBrowser ? 'ready' : 'loading')
  const [retryCount, setRetryCount] = useState(0)

  useEffect(() => {
    if (isBrowser) return
    let mounted = true
    let pollTimer: number | undefined
    const shouldPoll = loadState === defaultLoadState
    const checkRuntime = () => {
      loadState()
        .then(() => {
          if (mounted) setStatus('ready')
        })
        .catch(() => {
          if (mounted) setStatus('failed')
        })
    }
    setStatus('loading')
    checkRuntime()
    if (shouldPoll) pollTimer = window.setInterval(checkRuntime, 1000)
    return () => {
      mounted = false
      if (pollTimer !== undefined) window.clearInterval(pollTimer)
    }
  }, [isBrowser, loadState, retryCount])

  if (status === 'loading') {
    return <main className="desktop-startup-gate" aria-labelledby="desktop-startup-heading"><h1 id="desktop-startup-heading">Starting Codex Flow</h1><p role="status">Connecting to the local backend…</p></main>
  }

  if (status === 'failed') {
    const retryable = retryCount < MAX_MANUAL_RETRIES
    return (
      <main className="desktop-startup-gate" aria-labelledby="desktop-startup-heading">
        <h1 id="desktop-startup-heading">Codex Flow is unavailable</h1>
        <p role="alert">
          {retryable
            ? 'The local backend may still be starting. Retry connection while startup remains retryable.'
            : 'The local backend did not start after bounded retries. Restart the desktop app before trying again.'}
        </p>
        <p className="desktop-startup-gate__guidance">
          Open Diagnostics after the backend is available to review the safe log directory category. No filesystem path or token is shown here.
        </p>
        <button
          type="button"
          disabled={!retryable}
          onClick={() => setRetryCount((value) => value + 1)}
        >
          {retryable ? 'Retry connection' : 'Retry limit reached'}
        </button>
      </main>
    )
  }

  return <>{children}</>
}
