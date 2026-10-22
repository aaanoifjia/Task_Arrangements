import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { DiagnosticSummary } from '../../api/client'
import DiagnosticsPanel from './DiagnosticsPanel'

const summary: DiagnosticSummary = {
  app_version: '0.1.0', backend_version: '0.1.0', os_name: 'TestOS', os_release: '1.0',
  python_version: '3.11.9', db_schema_version: 3, db_path_category: 'configured',
  active_run_count: 1, active_task_count: 2, recent_error_event_types: ['TURN_FAILED'],
  log_directory_category: 'unavailable',
}

afterEach(() => { vi.restoreAllMocks() })

describe('DiagnosticsPanel', () => {
  it('shows safe summary metadata and downloads the diagnostic bundle', async () => {
    const user = userEvent.setup()
    const getDiagnostics = vi.fn().mockResolvedValue(summary)
    const downloadDiagnosticBundle = vi.fn().mockResolvedValue(new Blob(['zip']))
    const createObjectURL = vi.fn(() => 'blob:diagnostics')
    const revokeObjectURL = vi.fn()
    Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: createObjectURL })
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: revokeObjectURL })
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
    render(<DiagnosticsPanel api={{ getDiagnostics, downloadDiagnosticBundle }} />)

    expect(await screen.findByRole('heading', { name: 'Diagnostics' })).toBeInTheDocument()
    expect(screen.getByText('configured')).toBeInTheDocument()
    expect(screen.queryByText(/diagnostics\.sqlite3|secret-token|Bearer/i)).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Download diagnostic bundle' }))

    expect(downloadDiagnosticBundle).toHaveBeenCalledOnce()
    expect(createObjectURL).toHaveBeenCalledWith(expect.any(Blob))
    expect(click).toHaveBeenCalled()
  })

  it('shows load and download errors without inventing metadata', async () => {
    const user = userEvent.setup()
    const getDiagnostics = vi.fn().mockResolvedValue(summary)
    const downloadDiagnosticBundle = vi.fn().mockRejectedValue(new Error('bundle unavailable'))
    render(<DiagnosticsPanel api={{ getDiagnostics, downloadDiagnosticBundle }} />)

    await screen.findByRole('heading', { name: 'Diagnostics' })
    await user.click(screen.getByRole('button', { name: 'Download diagnostic bundle' }))

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('bundle unavailable'))
    expect(screen.getByText('configured')).toBeInTheDocument()
  })

  it('shows a visible load error', async () => {
    render(<DiagnosticsPanel api={{
      getDiagnostics: vi.fn().mockRejectedValue(new Error('offline')),
      downloadDiagnosticBundle: vi.fn(),
    }} />)

    expect(await screen.findByRole('alert')).toHaveTextContent('offline')
  })
})
