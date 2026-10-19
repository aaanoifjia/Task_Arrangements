import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { fixtureWorkflow } from '../../test/fixtures'
import { workflowToGraph } from './graphModel'
import WorkflowEditorLayout from './WorkflowEditorLayout'
import EditorEmptyState from './EditorEmptyState'

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

describe('EditorEmptyState', () => {
  it('shows onboarding instructions and adds the first task', () => {
    const onAddTask = vi.fn()
    render(<EditorEmptyState onAddTask={onAddTask} />)
    expect(screen.getByText(/Add a task, edit its Prompt and CWD, connect dependencies, Save, then Run/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Add Task' }))
    expect(onAddTask).toHaveBeenCalledOnce()
  })

  it('shows the empty state only for an empty graph', () => {
    globalThis.ResizeObserver = ResizeObserverMock
    const { rerender } = render(<WorkflowEditorLayout graph={{ nodes: [], edges: [] }} />)
    expect(screen.getByRole('heading', { name: 'Start your workflow' })).toBeInTheDocument()
    rerender(<WorkflowEditorLayout graph={workflowToGraph(fixtureWorkflow)} />)
    expect(screen.getByTestId('workflow-canvas')).toBeInTheDocument()
  })
})
