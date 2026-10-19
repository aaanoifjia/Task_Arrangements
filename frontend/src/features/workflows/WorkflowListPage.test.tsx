import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { fixtureWorkflowSummary } from '../../test/fixtures'
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
    render(<WorkflowListPage api={api({ list })} />)
    expect(await screen.findByText('No workflows yet.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Refresh' }))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('offline'))
  })
})
