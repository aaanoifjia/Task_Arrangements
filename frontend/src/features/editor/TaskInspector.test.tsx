import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { fixtureWorkflow } from '../../test/fixtures'
import { workflowToGraph } from './graphModel'
import WorkflowEditorLayout from './WorkflowEditorLayout'

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

describe('WorkflowEditorLayout', () => {
  it('shows guidance when no task is selected', () => {
    globalThis.ResizeObserver = ResizeObserverMock
    render(<WorkflowEditorLayout graph={workflowToGraph(fixtureWorkflow)} />)
    expect(screen.getByText('Select a task to inspect its configuration.')).toBeInTheDocument()
  })

  it('selects a task from the canvas and shows its inspector details', () => {
    globalThis.ResizeObserver = ResizeObserverMock
    render(<WorkflowEditorLayout graph={workflowToGraph(fixtureWorkflow)} />)
    fireEvent.click(screen.getByText('First task'))
    const inspector = screen.getByRole('complementary', { name: 'Task inspector' })
    expect(within(inspector).getByRole('heading', { name: 'Task inspector' })).toBeInTheDocument()
    expect(within(inspector).getByText('Task ID')).toBeInTheDocument()
    expect(within(inspector).getByText('A')).toBeInTheDocument()
  })
})
