import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import ContinuationFields from './ContinuationFields'

describe('ContinuationFields', () => {
  it('requires an explicit other task for continuation and clears it for new threads', () => {
    const onChange = vi.fn()
    const { rerender } = render(
      <ContinuationFields
        taskId="B"
        executionMode="NEW_THREAD"
        continueFromTaskId={null}
        availableTaskIds={['A', 'B', 'C']}
        onChange={onChange}
      />,
    )

    fireEvent.change(screen.getByLabelText('Execution mode'), { target: { value: 'CONTINUE_THREAD' } })
    expect(onChange).toHaveBeenLastCalledWith({ execution_mode: 'CONTINUE_THREAD', continue_from_task_id: null })
    rerender(
      <ContinuationFields
        taskId="B"
        executionMode="CONTINUE_THREAD"
        continueFromTaskId={null}
        availableTaskIds={['A', 'B', 'C']}
        onChange={onChange}
      />,
    )
    expect(screen.getByRole('alert')).toHaveTextContent('requires a source task')
    fireEvent.change(screen.getByLabelText('Continue from task'), { target: { value: 'A' } })
    expect(onChange).toHaveBeenLastCalledWith({ continue_from_task_id: 'A' })
    rerender(
      <ContinuationFields
        taskId="B"
        executionMode="CONTINUE_THREAD"
        continueFromTaskId="A"
        availableTaskIds={['A', 'B', 'C']}
        onChange={onChange}
      />,
    )
    fireEvent.change(screen.getByLabelText('Execution mode'), { target: { value: 'NEW_THREAD' } })
    expect(onChange).toHaveBeenLastCalledWith({ execution_mode: 'NEW_THREAD', continue_from_task_id: null })
  })

  it('does not offer the current task as a continuation source', () => {
    render(
      <ContinuationFields
        taskId="B"
        executionMode="CONTINUE_THREAD"
        continueFromTaskId="A"
        availableTaskIds={['A', 'B']}
        onChange={() => undefined}
      />,
    )
    expect(screen.getByLabelText('Continue from task')).not.toHaveValue('B')
    expect(screen.getByRole('option', { name: 'A' })).toBeInTheDocument()
  })
})
