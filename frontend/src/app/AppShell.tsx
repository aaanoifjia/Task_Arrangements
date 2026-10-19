import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import './AppShell.css'

type AppShellProps = { children: ReactNode }

function AppShell({ children }: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="app-shell__header">
        <NavLink className="app-shell__brand" to="/">Codex Flow</NavLink>
        <nav aria-label="Primary navigation" className="app-shell__nav">
          <NavLink to="/">Workflows</NavLink>
          <NavLink to="/runs">Runs</NavLink>
        </nav>
      </header>
      <main className="app-shell__content">{children}</main>
    </div>
  )
}

export default AppShell
