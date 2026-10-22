import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import type { SystemStatus } from '../../api/client'
import AboutPage from './AboutPage'

const status: SystemStatus = {
  service: 'ok', database: 'reachable', schema_version: 3, active_runtime_count: 2,
  app_version: '0.1.0', backend_version: '0.1.0', desktop_mode: true, runtime_available: true,
}

function renderPage(getSystemStatus: () => Promise<SystemStatus>) {
  return render(<MemoryRouter><AboutPage api={{ getSystemStatus }} /></MemoryRouter>)
}

describe('AboutPage', () => {
  it('shows a loading state before runtime status resolves', async () => {
    let resolve: (value: SystemStatus) => void = () => {}
    const getSystemStatus = vi.fn(() => new Promise<SystemStatus>((done) => { resolve = done }))
    renderPage(getSystemStatus)
    expect(screen.getByRole('status')).toHaveTextContent('Loading runtime status')
    resolve(status)
    await waitFor(() => expect(screen.getByText('Available')).toBeInTheDocument())
  })

  it('shows versions, runtime availability, and a Diagnostics link', async () => {
    renderPage(vi.fn().mockResolvedValue(status))

    expect(await screen.findByRole('heading', { name: 'About & Runtime' })).toBeInTheDocument()
    expect(screen.getAllByText('0.1.0')).toHaveLength(2)
    expect(screen.getByText('Enabled')).toBeInTheDocument()
    expect(screen.getByText('Available')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Open Diagnostics' })).toHaveAttribute('href', '/diagnostics')
  })

  it('shows an error when runtime status is unavailable', async () => {
    renderPage(vi.fn().mockRejectedValue(new Error('offline')))

    expect(await screen.findByRole('alert')).toHaveTextContent('offline')
  })
})
