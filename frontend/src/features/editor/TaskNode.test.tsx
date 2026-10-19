import { render, screen } from '@testing-library/react'
import { ReactFlowProvider } from '@xyflow/react'
import { describe, expect, it } from 'vitest'
import { fixtureWorkflow } from '../../test/fixtures'
import TaskNode from './TaskNode'

describe('TaskNode', () => {
  it('renders task metadata, handles, and selected state', () => {
    render(
      <ReactFlowProvider>
        <TaskNode data={{ task: fixtureWorkflow.tasks[0]! }} selected />
      </ReactFlowProvider>,
    )
    expect(screen.getByRole('article', { name: 'Task First task' })).toHaveClass('task-node--selected')
    expect(screen.getByText('First task')).toBeInTheDocument()
    expect(screen.getByText('A')).toBeInTheDocument()
    expect(screen.getByText('NEW_THREAD')).toBeInTheDocument()
    expect(screen.getByLabelText('Dependency input for A')).toBeInTheDocument()
    expect(screen.getByLabelText('Dependency output for A')).toBeInTheDocument()
  })
})
