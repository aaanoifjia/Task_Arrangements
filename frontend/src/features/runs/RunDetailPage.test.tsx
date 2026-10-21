import { act, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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
    await screen.findByRole('heading', { name: 'Tasks' })
    const taskSection = screen.getByRole('heading', { name: 'Tasks' }).parentElement!
    expect(within(taskSection).getByText('PENDING')).toBeInTheDocument()
    const socket = FakeWebSocket.instances[0]!
    act(() => socket.onmessage?.({ data: JSON.stringify({ kind: 'snapshot', payload: { tasks: [{ ...initialTask, status: 'RUNNING' }] } }) } as MessageEvent))
    expect(await within(taskSection).findByText('RUNNING')).toBeInTheDocument()
    act(() => socket.onmessage?.({ data: JSON.stringify({ kind: 'snapshot', payload: { tasks: [{ ...initialTask, status: 'SUCCESS' }] } }) } as MessageEvent))
    expect(await within(taskSection).findByText('SUCCESS')).toBeInTheDocument()
  })

  it('pauses and resumes through the durable RunApi and refreshes the snapshot', async () => {
    const user = userEvent.setup()
    const pause = vi.fn().mockResolvedValue({ accepted: true, action: 'PAUSE' })
    const resume = vi.fn().mockResolvedValue({ accepted: true, action: 'RESUME' })
    const runApi = api({ pause, resume })
    renderPage(runApi)

    expect(await screen.findByRole('heading', { name: 'Run run-1' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Pause' }))
    expect(pause).toHaveBeenCalledWith('run-1')
    expect(await screen.findByRole('button', { name: 'Resume' })).toBeInTheDocument()
    expect(runApi.get).toHaveBeenCalledTimes(2)
    expect(runApi.tasks).toHaveBeenCalledTimes(2)

    await user.click(screen.getByRole('button', { name: 'Resume' }))
    expect(resume).toHaveBeenCalledWith('run-1')
    expect(await screen.findByRole('button', { name: 'Pause' })).toBeInTheDocument()
  })

  it('shows a stable pause error and clears pending state when the API rejects', async () => {
    const user = userEvent.setup()
    const pause = vi.fn().mockRejectedValue(new Error('pause conflict'))
    const runApi = api({ pause })
    renderPage(runApi)

    await screen.findByRole('heading', { name: 'Run run-1' })
    await user.click(screen.getByRole('button', { name: 'Pause' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('pause conflict')
    expect(screen.getByRole('button', { name: 'Pause' })).not.toBeDisabled()
  })
})
