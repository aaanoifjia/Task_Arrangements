import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { fixtureRunDetail, fixtureTaskRun } from '../../test/fixtures'
import RunGraph from './RunGraph'

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

describe('RunGraph', () => {
  it('renders the immutable snapshot graph with task-run status and no editing controls', () => {
    globalThis.ResizeObserver = ResizeObserverMock
    render(
      <RunGraph
        snapshot={{
          ...fixtureRunDetail.snapshot,
          tasks: [{ id: 'A', name: 'First task' }, { id: 'B', name: 'Second task' }],
          edges: [{ source_task_id: 'A', target_task_id: 'B' }],
        }}
        taskRuns={[fixtureTaskRun]}
      />,
    )
    expect(screen.getByTestId('run-graph')).toHaveAttribute('data-read-only', 'true')
    expect(screen.getByText('First task — RUNNING')).toBeInTheDocument()
    expect(screen.getByText('Second task — PENDING')).toBeInTheDocument()
    expect(screen.getByTestId('rf__minimap')).toBeInTheDocument()
  })
})
