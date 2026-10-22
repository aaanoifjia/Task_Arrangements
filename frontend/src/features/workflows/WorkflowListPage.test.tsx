import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { fixtureWorkflowSummary } from '../../test/fixtures'
import { STARTER_WORKFLOWS } from '../../samples/workflows'
import type { WorkflowApi } from './api'
import WorkflowListPage from './WorkflowListPage'

function api(overrides: Partial<WorkflowApi> = {}): WorkflowApi {
  return { list: vi.fn().mockResolvedValue([fixtureWorkflowSummary]), get: vi.fn(), create: vi.fn(), update: vi.fn(), ...overrides }
}

describe('WorkflowListPage', () => {
  it('loads workflows and links to the editor', async () => {
    render(<MemoryRouter><WorkflowListPage api={api()} /></MemoryRouter>)
    expect(screen.getByRole('status')).toHaveTextContent('Loading')
    expect(await screen.findByText(fixtureWorkflowSummary.name)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Example workflow/ })).toHaveAttribute('href', '/workflows/workflow-1')
  })

  it('shows empty and error states and supports refresh', async () => {
    const list = vi.fn().mockResolvedValueOnce([]).mockRejectedValueOnce(new Error('offline'))
    const user = userEvent.setup()
    render(<MemoryRouter><WorkflowListPage api={api({ list })} /></MemoryRouter>)
    expect(await screen.findByRole('heading', { name: 'Start your first workflow' })).toBeInTheDocument()
    expect(screen.getByText('No workflows yet. Create one from scratch or try a safe sample.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Create workflow' }))
    expect(screen.getByRole('heading', { name: 'New workflow' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Refresh' }))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('offline'))
  })

  it('exposes a keyboard-usable sample action callback', async () => {
    const onTrySample = vi.fn()
    const user = userEvent.setup()
    render(<MemoryRouter><WorkflowListPage api={api({ list: vi.fn().mockResolvedValue([]) })} onTrySample={onTrySample} /></MemoryRouter>)
    await screen.findByRole('heading', { name: 'Start your first workflow' })
    await user.click(screen.getByRole('button', { name: 'Try a sample' }))
    expect(onTrySample).toHaveBeenCalledOnce()
  })

  it('creates a materialized sample through the API and opens the returned editor route', async () => {
    const create = vi.fn().mockImplementation(async (workflow) => ({ workflow }))
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<WorkflowListPage api={api({ list: vi.fn().mockResolvedValue([]), create })} />} />
          <Route path="/workflows/:workflowId" element={<p>editor route</p>} />
        </Routes>
      </MemoryRouter>,
    )

    await screen.findByRole('heading', { name: 'Start your first workflow' })
    await user.click(screen.getByRole('button', { name: 'Try a sample' }))
    await user.click(screen.getByRole('radio', { name: /Linear starter/ }))
    await user.click(screen.getByRole('button', { name: 'Use selected sample' }))

    await screen.findByText('editor route')
    expect(create).toHaveBeenCalledWith(expect.objectContaining({
      id: 'sample-linear-copy',
      tasks: STARTER_WORKFLOWS[0].tasks,
    }))
  })
})
