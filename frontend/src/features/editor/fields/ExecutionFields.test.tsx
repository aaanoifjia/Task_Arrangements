import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import ExecutionFields from './ExecutionFields'

describe('ExecutionFields', () => {
  it('round-trips all sandbox values and nullable approval mode', () => {
    const onChange = vi.fn()
    const { rerender } = render(<ExecutionFields sandbox="workspace_write" approvalMode={null} onChange={onChange} />)

    fireEvent.change(screen.getByLabelText('Sandbox'), { target: { value: 'read_only' } })
    expect(onChange).toHaveBeenLastCalledWith({ sandbox: 'read_only' })
    fireEvent.change(screen.getByLabelText('Sandbox'), { target: { value: 'full_access' } })
    expect(onChange).toHaveBeenLastCalledWith({ sandbox: 'full_access' })
    fireEvent.change(screen.getByLabelText('Approval mode'), { target: { value: 'ask' } })
    expect(onChange).toHaveBeenLastCalledWith({ approval_mode: 'ask' })
    rerender(<ExecutionFields sandbox="full_access" approvalMode="ask" onChange={onChange} />)
    fireEvent.change(screen.getByLabelText('Approval mode'), { target: { value: '' } })
    expect(onChange).toHaveBeenLastCalledWith({ approval_mode: null })
  })

  it('does not replace an explicit sandbox or approval value with a UI default', () => {
    render(<ExecutionFields sandbox="full_access" approvalMode="never" onChange={() => undefined} />)
    expect(screen.getByLabelText('Sandbox')).toHaveValue('full_access')
    expect(screen.getByLabelText('Approval mode')).toHaveValue('never')
  })
})
