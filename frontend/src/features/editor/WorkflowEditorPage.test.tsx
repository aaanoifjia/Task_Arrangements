import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { fixtureWorkflowDetail } from '../../test/fixtures'
import type { WorkflowApi } from '../workflows/api'
import WorkflowEditorPage from './WorkflowEditorPage'

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

function renderPage(api: WorkflowApi) {
  globalThis.ResizeObserver = ResizeObserverMock
  window.ResizeObserver = ResizeObserverMock
  return render(
    <MemoryRouter initialEntries={['/workflows/workflow-1']}>
      <Routes><Route path="/workflows/:workflowId" element={<WorkflowEditorPage api={api} />} /></Routes>
    </MemoryRouter>,
  )
}

describe('WorkflowEditorPage', () => {
  it('loads the route workflow into the editor', async () => {
    const api = { get: vi.fn().mockResolvedValue(fixtureWorkflowDetail) } as unknown as WorkflowApi
    renderPage(api)
    expect(await screen.findByRole('heading', { name: 'Example workflow' })).toBeInTheDocument()
    expect(screen.getByText('First task')).toBeInTheDocument()
    expect(api.get).toHaveBeenCalledWith('workflow-1')
  })

  it('renders a not-found state for a 404 response', async () => {
    const error = Object.assign(new Error('missing'), { status: 404 })
    const api = { get: vi.fn().mockRejectedValue(error) } as unknown as WorkflowApi
    renderPage(api)
    expect(await screen.findByRole('heading', { name: 'Workflow not found' })).toBeInTheDocument()
  })

  it('renders an API error without leaving the shell', async () => {
    const api = { get: vi.fn().mockRejectedValue(new Error('server unavailable')) } as unknown as WorkflowApi
    renderPage(api)
    expect(await screen.findByRole('heading', { name: 'Unable to load workflow' })).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('server unavailable')
  })
})
