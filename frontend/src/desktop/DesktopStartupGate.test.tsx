import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import DesktopStartupGate from './DesktopStartupGate'

describe('DesktopStartupGate', () => {
  it('blocks normal routes while the desktop runtime is loading', () => {
    const loadState = vi.fn(() => new Promise<null>(() => undefined))
    render(<DesktopStartupGate loadState={loadState}><p>normal route</p></DesktopStartupGate>)

    expect(screen.getByRole('status')).toHaveTextContent('Connecting to the local backend')
    expect(screen.queryByText('normal route')).not.toBeInTheDocument()
  })

  it('releases normal routes after the runtime is ready', async () => {
    render(<DesktopStartupGate loadState={async () => null}><p>normal route</p></DesktopStartupGate>)

    await waitFor(() => expect(screen.getByText('normal route')).toBeInTheDocument())
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('shows an actionable local error without exposing the failure detail', async () => {
    render(<DesktopStartupGate loadState={async () => { throw new Error('secret token and stack trace') }}><p>normal route</p></DesktopStartupGate>)

    expect(await screen.findByRole('heading', { name: 'Codex Flow is unavailable' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Retry connection' })).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('may still be starting')
    expect(screen.getByText(/safe log directory category/i)).toBeInTheDocument()
    expect(screen.queryByText(/secret token|stack trace/i)).not.toBeInTheDocument()
    expect(screen.queryByText('normal route')).not.toBeInTheDocument()
  })

  it('recovers after a temporary backend restart when retry succeeds', async () => {
    const loadState = vi.fn()
      .mockRejectedValueOnce(new Error('backend unavailable'))
      .mockResolvedValueOnce(null)
    const user = userEvent.setup()
    render(<DesktopStartupGate loadState={loadState}><p>normal route</p></DesktopStartupGate>)

    expect(await screen.findByRole('heading', { name: 'Codex Flow is unavailable' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Retry connection' }))
    expect(await screen.findByText('normal route')).toBeInTheDocument()
    expect(loadState).toHaveBeenCalledTimes(2)
  })

  it('stops after bounded retries and explains persistent startup failure', async () => {
    const loadState = vi.fn().mockRejectedValue(new Error('backend unavailable'))
    const user = userEvent.setup()
    render(<DesktopStartupGate loadState={loadState}><p>normal route</p></DesktopStartupGate>)

    expect(await screen.findByRole('heading', { name: 'Codex Flow is unavailable' })).toBeInTheDocument()
    for (let retry = 0; retry < 3; retry += 1) {
      await user.click(screen.getByRole('button', { name: 'Retry connection' }))
      await screen.findByRole('button', { name: retry === 2 ? 'Retry limit reached' : 'Retry connection' })
    }
    expect(screen.getByRole('alert')).toHaveTextContent('after bounded retries')
    expect(screen.getByRole('button', { name: 'Retry limit reached' })).toBeDisabled()
    expect(loadState).toHaveBeenCalledTimes(4)
  })
})
