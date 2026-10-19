import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ReactFlowProvider } from '@xyflow/react'
import { describe, expect, it, vi } from 'vitest'
import { fixtureRunDetail, fixtureTaskRun } from '../test/fixtures'
import WorkflowEditorLayout from '../features/editor/WorkflowEditorLayout'
import RunGraph from '../features/runs/RunGraph'
import TaskRunDrawer from '../features/runs/TaskRunDrawer'

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

describe('M7 accessibility interactions', () => {
  it('keeps editor onboarding and graph-adjacent controls labeled and reachable', async () => {
    const user = userEvent.setup()
    render(<WorkflowEditorLayout graph={{ nodes: [], edges: [] }} onAddTask={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Add Task' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'View workflow runs' })).toHaveAttribute('href', '/runs?workflow_id=new-workflow')

    globalThis.ResizeObserver = ResizeObserverMock
    render(<RunGraph snapshot={{ ...fixtureRunDetail.snapshot, tasks: [{ id: 'A', name: 'First task' }], edges: [] }} taskRuns={[fixtureTaskRun]} />)
    await user.tab()
    expect(screen.getByRole('button', { name: 'Zoom In' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Fit View' })).toBeInTheDocument()
  })

  it('exposes task details as a labeled dialog with keyboard controls', async () => {
    const user = userEvent.setup()
    render(
      <ReactFlowProvider>
        <TaskRunDrawer task={fixtureTaskRun} onClose={vi.fn()} attemptApi={{ attempts: vi.fn().mockResolvedValue([]) }} />
      </ReactFlowProvider>,
    )
    expect(screen.getByRole('dialog', { name: 'Task A' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Close task details' })).toBeInTheDocument()
    expect(await screen.findByText('No attempts recorded.')).toBeInTheDocument()
    await user.tab()
    expect(screen.getByRole('button', { name: 'Close task details' })).toHaveFocus()
  })
})
