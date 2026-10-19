import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { fixtureRunSummary } from '../../test/fixtures'
import type { RunApi } from './api'
import RunListPage from './RunListPage'

function api(overrides: Partial<RunApi> = {}): RunApi {
  return {
    list: vi.fn().mockResolvedValue([fixtureRunSummary, { ...fixtureRunSummary, id: 'run-2', workflow_id: 'other-workflow' }]),
    start: vi.fn(), get: vi.fn(), tasks: vi.fn(), attempts: vi.fn(), ...overrides,
  }
}

describe('RunListPage', () => {
  it('lists run metadata and links each run to its detail page', async () => {
    render(<MemoryRouter><RunListPage api={api()} /></MemoryRouter>)
    expect(await screen.findByText('run-1')).toBeInTheDocument()
    const runLink = screen.getByRole('link', { name: /run-1/ })
    expect(within(runLink).getByText('Workflow: workflow-1')).toBeInTheDocument()
    expect(within(runLink).getByText('Status: RUNNING')).toBeInTheDocument()
    expect(within(runLink).getByText(fixtureRunSummary.created_at)).toBeInTheDocument()
    expect(runLink).toHaveAttribute('href', '/runs/run-1')
  })

  it('filters runs by the workflow_id query parameter', async () => {
    const list = vi.fn().mockResolvedValue([
      fixtureRunSummary,
      { ...fixtureRunSummary, id: 'run-2', workflow_id: 'other-workflow' },
    ])
    render(<MemoryRouter initialEntries={['/runs?workflow_id=workflow-1']}><RunListPage api={api({ list })} /></MemoryRouter>)
    expect(await screen.findByText('run-1')).toBeInTheDocument()
    expect(screen.queryByText('run-2')).not.toBeInTheDocument()
    expect(within(screen.getByRole('link', { name: /run-1/ })).getByText('Workflow: workflow-1')).toBeInTheDocument()
  })

  it('renders empty and error states and supports refresh', async () => {
    const list = vi.fn().mockResolvedValueOnce([]).mockRejectedValueOnce(new Error('offline'))
    const user = userEvent.setup()
    render(<MemoryRouter><RunListPage api={api({ list })} /></MemoryRouter>)
    expect(await screen.findByText('No runs yet.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Refresh' }))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('offline'))
  })
})
