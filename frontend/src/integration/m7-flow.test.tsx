import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import type { EventView } from '../api/types'
import type { RunApi } from '../features/runs/api'
import RunDetailPage from '../features/runs/RunDetailPage'
import WorkflowEditorPage from '../features/editor/WorkflowEditorPage'
import WorkflowListPage from '../features/workflows/WorkflowListPage'
import type { WorkflowApi } from '../features/workflows/api'
import { fixtureAttempt, fixtureRunDetail, fixtureTaskRun, fixtureWorkflowDetail, fixtureWorkflowSummary } from '../test/fixtures'

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

class FakeWebSocket {
  static instances: FakeWebSocket[] = []
  onmessage: ((event: MessageEvent) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  constructor(readonly url: string) { FakeWebSocket.instances.push(this) }
  close() {}
}

describe('M7 mocked user flow', () => {
  it('creates, edits, validates, saves, starts, streams, inspects and opens a run', async () => {
    globalThis.ResizeObserver = ResizeObserverMock
    FakeWebSocket.instances = []
    const user = userEvent.setup()
    const workflowApi: WorkflowApi = {
      list: vi.fn().mockResolvedValue([fixtureWorkflowSummary]),
      get: vi.fn().mockResolvedValue(fixtureWorkflowDetail),
      create: vi.fn().mockResolvedValue(fixtureWorkflowDetail),
      update: vi.fn().mockResolvedValue(fixtureWorkflowDetail),
    }
    const runDetail = {
      ...fixtureRunDetail,
      status: 'SUCCESS' as const,
      snapshot: {
        ...fixtureRunDetail.snapshot,
        tasks: [{ id: 'A', name: 'First task' }, { id: 'B', name: 'Second task' }],
        edges: [{ source_task_id: 'A', target_task_id: 'B' }],
      },
    }
    const initialTask = { ...fixtureTaskRun, status: 'PENDING' as const }
    const liveTask = { ...initialTask, status: 'SUCCESS' as const }
    const event: EventView = {
      id: 'event-live', workflow_run_id: 'run-1', task_run_id: initialTask.id,
      attempt_id: fixtureAttempt.id, event_type: 'TURN_COMPLETED', payload: { status: 'completed' }, created_at: 'now',
    }
    const runApi: RunApi = {
      start: vi.fn().mockResolvedValue({ run_id: 'run-1' }),
      list: vi.fn().mockResolvedValue([fixtureRunDetail]),
      get: vi.fn().mockResolvedValue(runDetail),
      tasks: vi.fn().mockResolvedValue([initialTask]),
      attempts: vi.fn().mockResolvedValue([fixtureAttempt]),
    }

    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<WorkflowListPage api={workflowApi} />} />
          <Route path="/workflows/:workflowId" element={<WorkflowEditorPage api={workflowApi} runApi={runApi} />} />
          <Route path="/runs/:runId" element={<RunDetailPage api={runApi} streamOptions={{ webSocketFactory: FakeWebSocket }} />} />
        </Routes>
      </MemoryRouter>,
    )

    await user.click(await screen.findByRole('button', { name: 'New workflow' }))
    await user.type(screen.getByLabelText('Workflow id'), 'workflow-1')
    await user.type(screen.getByLabelText('Name'), 'Example workflow')
    await user.click(screen.getByRole('button', { name: 'Create workflow' }))
    expect(await screen.findByRole('heading', { name: 'Example workflow' })).toBeInTheDocument()

    fireEvent.click(await screen.findByTestId('rf__node-A'))
    const prompt = screen.getByLabelText('Task prompt')
    await user.clear(prompt)
    await user.type(prompt, 'Updated prompt')
    const saveButtons = screen.getAllByRole('button', { name: 'Save workflow' })
    await user.click(saveButtons[saveButtons.length - 1]!)
    await waitFor(() => expect(workflowApi.update).toHaveBeenCalled())
    expect(screen.getByText('Workflow is valid.')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Start run' }))
    expect(runApi.start).toHaveBeenCalledWith('workflow-1')
    expect(await screen.findByRole('heading', { name: 'Run run-1' })).toBeInTheDocument()
    expect(screen.getByTestId('run-result')).toHaveTextContent('Run result: SUCCESS')

    const socket = FakeWebSocket.instances[FakeWebSocket.instances.length - 1]!
    act(() => socket.onmessage?.({ data: JSON.stringify({ kind: 'snapshot', payload: { tasks: [liveTask] } }) } as MessageEvent))
    act(() => socket.onmessage?.({ data: JSON.stringify({ kind: 'event', payload: event }) } as MessageEvent))
    const eventLog = await screen.findByRole('region', { name: 'Event log' })
    const eventItem = within(eventLog).getByRole('listitem')
    expect(within(eventItem).getByText('TURN_COMPLETED')).toBeInTheDocument()
    expect(screen.getByTestId('run-status')).toHaveTextContent('SUCCESS')

    fireEvent.click(screen.getByTestId('rf__node-A'))
    expect(await screen.findByRole('dialog', { name: 'Task A' })).toBeInTheDocument()
    expect(await screen.findByText('attempt-1')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Open in Codex' })).toHaveAttribute('href', 'codex://threads/thread-1')
  })
})
