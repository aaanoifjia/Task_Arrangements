import { act, render, screen, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { fixtureRunDetail, fixtureTaskRun } from '../../test/fixtures'
import type { RunApi } from './api'
import RunDetailPage from './RunDetailPage'

class FakeWebSocket {
  static instances: FakeWebSocket[] = []
  onmessage: ((event: MessageEvent) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  constructor(readonly url: string) { FakeWebSocket.instances.push(this) }
  close() {}
}

function api(overrides: Partial<RunApi> = {}): RunApi {
  return {
    start: vi.fn(), list: vi.fn(), get: vi.fn().mockResolvedValue(fixtureRunDetail),
    tasks: vi.fn().mockResolvedValue([fixtureTaskRun]), attempts: vi.fn(), ...overrides,
  }
}

function renderPage(runApi: RunApi, streamOptions?: { webSocketFactory: typeof FakeWebSocket }) {
  return render(
    <MemoryRouter initialEntries={['/runs/run-1']}>
      <Routes><Route path="/runs/:runId" element={<RunDetailPage api={runApi} streamOptions={streamOptions} />} /></Routes>
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

  it('applies PENDING to RUNNING to SUCCESS live task snapshots', async () => {
    FakeWebSocket.instances = []
    const initialTask = { ...fixtureTaskRun, status: 'PENDING' as const }
    const runApi = api({ tasks: vi.fn().mockResolvedValue([initialTask]) })
    renderPage(runApi, { webSocketFactory: FakeWebSocket })
    expect(await screen.findByText('PENDING')).toBeInTheDocument()
    const taskSection = screen.getByRole('heading', { name: 'Tasks' }).parentElement!
    const socket = FakeWebSocket.instances[0]!
    act(() => socket.onmessage?.({ data: JSON.stringify({ kind: 'snapshot', payload: { tasks: [{ ...initialTask, status: 'RUNNING' }] } }) } as MessageEvent))
    expect(await within(taskSection).findByText('RUNNING')).toBeInTheDocument()
    act(() => socket.onmessage?.({ data: JSON.stringify({ kind: 'snapshot', payload: { tasks: [{ ...initialTask, status: 'SUCCESS' }] } }) } as MessageEvent))
    expect(await within(taskSection).findByText('SUCCESS')).toBeInTheDocument()
  })
})
