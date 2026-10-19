import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { fixtureRunDetail, fixtureTaskRun } from '../../test/fixtures'
import type { RunApi } from './api'
import RunDetailPage from './RunDetailPage'

function api(overrides: Partial<RunApi> = {}): RunApi {
  return {
    start: vi.fn(), list: vi.fn(), get: vi.fn().mockResolvedValue(fixtureRunDetail),
    tasks: vi.fn().mockResolvedValue([fixtureTaskRun]), attempts: vi.fn(), ...overrides,
  }
}

function renderPage(runApi: RunApi) {
  return render(
    <MemoryRouter initialEntries={['/runs/run-1']}>
      <Routes><Route path="/runs/:runId" element={<RunDetailPage api={runApi} />} /></Routes>
    </MemoryRouter>,
  )
}

describe('RunDetailPage', () => {
  it('shows loading, run metadata, and the task snapshot', async () => {
    const runApi = api()
    renderPage(runApi)
    expect(screen.getByRole('status')).toHaveTextContent('Loading run')
    expect(await screen.findByRole('heading', { name: 'Run run-1' })).toBeInTheDocument()
    expect(screen.getByTestId('run-status')).toHaveTextContent('RUNNING')
    expect(screen.getByText('Workflow: workflow-1')).toBeInTheDocument()
    expect(screen.getByText('A')).toBeInTheDocument()
    expect(runApi.get).toHaveBeenCalledWith('run-1')
    expect(runApi.tasks).toHaveBeenCalledWith('run-1')
  })

  it('renders a not-found state for a 404 response', async () => {
    const error = Object.assign(new Error('missing'), { status: 404 })
    renderPage(api({ get: vi.fn().mockRejectedValue(error) }))
    expect(await screen.findByRole('heading', { name: 'Run not found' })).toBeInTheDocument()
  })
})
