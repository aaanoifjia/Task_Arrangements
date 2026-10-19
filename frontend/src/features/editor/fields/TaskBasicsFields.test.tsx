import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { fixtureWorkflow } from '../../../test/fixtures'
import { workflowToGraph } from '../graphModel'
import TaskBasicsFields, { renameTaskInGraph } from './TaskBasicsFields'

describe('TaskBasicsFields', () => {
  it('commits valid name, cwd, and identity updates', () => {
    const onChange = vi.fn()
    render(<TaskBasicsFields task={fixtureWorkflow.tasks[0]!} existingTaskIds={['A', 'B']} onChange={onChange} />)

    fireEvent.change(screen.getByLabelText('Task ID'), { target: { value: 'C' } })
    fireEvent.blur(screen.getByLabelText('Task ID'))
    fireEvent.change(screen.getByLabelText('Task name'), { target: { value: 'Renamed' } })
    fireEvent.blur(screen.getByLabelText('Task name'))
    fireEvent.change(screen.getByLabelText('Working directory'), { target: { value: 'workspace' } })
    fireEvent.blur(screen.getByLabelText('Working directory'))

    expect(onChange).toHaveBeenNthCalledWith(1, { id: 'C' })
    expect(onChange).toHaveBeenNthCalledWith(2, { name: 'Renamed' })
    expect(onChange).toHaveBeenNthCalledWith(3, { cwd: 'workspace' })
  })

  it('rejects blank and duplicate task IDs', () => {
    const onChange = vi.fn()
    render(<TaskBasicsFields task={fixtureWorkflow.tasks[0]!} existingTaskIds={['A', 'B']} onChange={onChange} />)

    fireEvent.change(screen.getByLabelText('Task ID'), { target: { value: '' } })
    fireEvent.blur(screen.getByLabelText('Task ID'))
    expect(screen.getByRole('alert')).toHaveTextContent('Task ID is required.')
    fireEvent.change(screen.getByLabelText('Task ID'), { target: { value: 'B' } })
    fireEvent.blur(screen.getByLabelText('Task ID'))
    expect(screen.getByRole('alert')).toHaveTextContent('Task ID must be unique.')
    expect(onChange).not.toHaveBeenCalled()
  })

  it('updates node IDs, edge endpoints, and dependency references together', () => {
    const renamed = renameTaskInGraph(workflowToGraph(fixtureWorkflow), 'A', 'C')
    expect(renamed.nodes.map((node) => node.id)).toEqual(['C', 'B'])
    expect(renamed.edges).toEqual([{ id: 'C->B', source: 'C', target: 'B' }])
    expect(renamed.nodes[1]?.data.task.dependencies).toEqual(['C'])
  })
})
