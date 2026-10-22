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
    listPage: vi.fn().mockResolvedValue({
      items: [fixtureRunSummary, { ...fixtureRunSummary, id: 'run-2', workflow_id: 'other-workflow' }],
      next_cursor: null,
    }),
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
    const listPage = vi.fn().mockResolvedValue({
      items: [
      fixtureRunSummary,
      { ...fixtureRunSummary, id: 'run-2', workflow_id: 'other-workflow' },
      ], next_cursor: null,
    })
    render(<MemoryRouter initialEntries={['/runs?workflow_id=workflow-1']}><RunListPage api={api({ listPage })} /></MemoryRouter>)
    expect(await screen.findByText('run-1')).toBeInTheDocument()
    expect(screen.queryByText('run-2')).not.toBeInTheDocument()
    expect(within(screen.getByRole('link', { name: /run-1/ })).getByText('Workflow: workflow-1')).toBeInTheDocument()
  })

  it('renders empty and error states and supports refresh', async () => {
    const listPage = vi.fn().mockResolvedValueOnce({ items: [], next_cursor: null }).mockRejectedValueOnce(new Error('offline'))
    const user = userEvent.setup()
    render(<MemoryRouter><RunListPage api={api({ listPage })} /></MemoryRouter>)
    expect(await screen.findByText('No runs yet.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Refresh' }))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('offline'))
  })

  it('appends a page without duplicate runs and hides Load more at the end', async () => {
    const user = userEvent.setup()
    const secondRun = { ...fixtureRunSummary, id: 'run-2' }
    const listPage = vi.fn()
      .mockResolvedValueOnce({ items: [fixtureRunSummary], next_cursor: 'cursor-1' })
      .mockResolvedValueOnce({ items: [fixtureRunSummary, secondRun], next_cursor: null })
    render(<MemoryRouter><RunListPage api={api({ listPage })} /></MemoryRouter>)

    expect(await screen.findByText('run-1')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Load more' }))
    expect(await screen.findByText('run-2')).toBeInTheDocument()
    expect(screen.getAllByText('run-1')).toHaveLength(1)
    expect(screen.queryByRole('button', { name: 'Load more' })).not.toBeInTheDocument()
  })

  it('keeps loaded runs visible and reports a Load more error', async () => {
    const user = userEvent.setup()
    const listPage = vi.fn()
      .mockResolvedValueOnce({ items: [fixtureRunSummary], next_cursor: 'cursor-1' })
      .mockRejectedValueOnce(new Error('offline'))
    render(<MemoryRouter><RunListPage api={api({ listPage })} /></MemoryRouter>)

    expect(await screen.findByText('run-1')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Load more' }))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('offline'))
    expect(screen.getByText('run-1')).toBeInTheDocument()
  })
})
