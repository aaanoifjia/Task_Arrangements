import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { fixtureWorkflow } from '../../test/fixtures'
import { workflowToGraph } from './graphModel'
import WorkflowCanvas from './WorkflowCanvas'

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

describe('WorkflowCanvas', () => {
  it('mounts the fixture graph with stable node IDs', () => {
    globalThis.ResizeObserver = ResizeObserverMock
    render(<WorkflowCanvas graph={workflowToGraph(fixtureWorkflow)} />)
    expect(screen.getByTestId('workflow-canvas')).toBeInTheDocument()
    expect(screen.getByText('First task')).toBeInTheDocument()
    expect(screen.getByText('Second task')).toBeInTheDocument()
    expect(screen.getByTestId('rf__minimap')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Fit View' }))
  })
})
