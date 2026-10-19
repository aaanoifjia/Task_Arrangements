import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { fixtureRunDetail, fixtureTaskRun } from '../../test/fixtures'
import RunGraph from './RunGraph'

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

describe('RunGraph', () => {
  it('renders a mixed-state immutable graph with status and execution references', () => {
    globalThis.ResizeObserver = ResizeObserverMock
    render(
      <RunGraph
        snapshot={{
          ...fixtureRunDetail.snapshot,
          tasks: [{ id: 'A', name: 'First task' }, { id: 'B', name: 'Second task' }],
          edges: [{ source_task_id: 'A', target_task_id: 'B' }],
        }}
        taskRuns={[
          fixtureTaskRun,
          { ...fixtureTaskRun, id: 'task-run-b', task_id: 'B', status: 'FAILED', thread_id: 'thread-b', turn_id: 'turn-b' },
        ]}
      />,
    )
    expect(screen.getByTestId('run-graph')).toHaveAttribute('data-read-only', 'true')
    expect(screen.getByText('First task')).toBeInTheDocument()
    expect(screen.getByText('Running')).toBeInTheDocument()
    expect(screen.getByText('Second task')).toBeInTheDocument()
    expect(screen.getByText('Failed')).toBeInTheDocument()
    expect(screen.getByText('Thread: thread-b')).toBeInTheDocument()
    expect(screen.getByText('Turn: turn-b')).toBeInTheDocument()
    expect(screen.getByTestId('rf__minimap')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('rf__node-A'))
    expect(screen.getByTestId('task-run-drawer')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Task A' })).toBeInTheDocument()
  })
})
