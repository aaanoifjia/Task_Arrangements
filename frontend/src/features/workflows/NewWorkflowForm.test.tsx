import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import type { WorkflowApi } from './api'
import NewWorkflowForm from './NewWorkflowForm'

function api(create = vi.fn()): WorkflowApi {
  return { list: vi.fn(), get: vi.fn(), create, update: vi.fn() }
}

describe('NewWorkflowForm', () => {
  it('validates required identity before POST', async () => {
    const create = vi.fn()
    const user = userEvent.setup()
    render(<MemoryRouter><NewWorkflowForm api={api(create)} /></MemoryRouter>)
    await user.click(screen.getByRole('button', { name: 'Create workflow' }))
    expect(screen.getByRole('alert')).toHaveTextContent('id and name are required')
    expect(create).not.toHaveBeenCalled()
  })

  it('persists an empty workflow and navigates only after success', async () => {
    const create = vi.fn().mockResolvedValue({ workflow: { id: 'new', name: 'New', description: null, tasks: [], edges: [] } })
    const user = userEvent.setup()
    render(<MemoryRouter><NewWorkflowForm api={api(create)} /></MemoryRouter>)
    await user.type(screen.getByLabelText('Workflow id'), 'new')
    await user.type(screen.getByLabelText('Name'), 'New')
    await user.click(screen.getByRole('button', { name: 'Create workflow' }))
    expect(create).toHaveBeenCalledWith(expect.objectContaining({ id: 'new', tasks: [], edges: [] }))
  })
})
