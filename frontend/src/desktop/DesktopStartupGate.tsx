import { useEffect, useState, type ReactNode } from 'react'
import { isTauriEnvironment, loadRuntimeState, type DesktopRuntimeState } from './runtime'
import './DesktopStartupGate.css'

type StartupState = 'loading' | 'ready' | 'failed'

const defaultLoadState = () => loadRuntimeState()

export type DesktopStartupGateProps = {
  children: ReactNode
  loadState?: () => Promise<DesktopRuntimeState | null>
}

export default function DesktopStartupGate({ children, loadState = defaultLoadState }: DesktopStartupGateProps) {
  const isBrowser = loadState === defaultLoadState && !isTauriEnvironment()
  const [status, setStatus] = useState<StartupState>(isBrowser ? 'ready' : 'loading')
  const [attempt, setAttempt] = useState(0)

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
  }, [attempt, isBrowser, loadState])

  if (status === 'loading') {
    return <main className="desktop-startup-gate" aria-labelledby="desktop-startup-heading"><h1 id="desktop-startup-heading">Starting Codex Flow</h1><p role="status">Connecting to the local backend…</p></main>
  }

  if (status === 'failed') {
    return <main className="desktop-startup-gate" aria-labelledby="desktop-startup-heading"><h1 id="desktop-startup-heading">Codex Flow is unavailable</h1><p>The local backend did not start. Restart the desktop app and try again.</p><button type="button" onClick={() => setAttempt((value) => value + 1)}>Retry connection</button></main>
  }

  return <>{children}</>
}
