import type { ReactNode } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import AttentionCenter from '../features/attention/AttentionCenter'
import DiagnosticsPanel from '../features/system/DiagnosticsPanel'
import './AppShell.css'

type AppShellProps = { children: ReactNode; diagnosticsApi?: Parameters<typeof DiagnosticsPanel>[0]['api'] }

function AppShell({ children, diagnosticsApi }: AppShellProps) {
  const location = useLocation()
  return (
    <div className="app-shell">
      <header className="app-shell__header">
        <NavLink className="app-shell__brand" to="/">Codex Flow</NavLink>
        <nav aria-label="Primary navigation" className="app-shell__nav">
          <NavLink to="/">Workflows</NavLink>
          <NavLink to="/runs">Runs</NavLink>
          <NavLink to="/about">About</NavLink>
          <NavLink to="/diagnostics">Diagnostics</NavLink>
        </nav>
        <AttentionCenter />
      </header>
      <main className="app-shell__content">
        {location.pathname === '/diagnostics' ? <DiagnosticsPanel api={diagnosticsApi} /> : children}
      </main>
    </div>
  )
}

export default AppShell
