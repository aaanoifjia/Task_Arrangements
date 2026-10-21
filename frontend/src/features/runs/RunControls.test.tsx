import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import RunControls from './RunControls'

const callbacks = () => ({
  onPause: vi.fn(), onResume: vi.fn(), onRetry: vi.fn(),
  onCancel: vi.fn(), onSkip: vi.fn(), onMarkSuccess: vi.fn(),
})

describe('RunControls', () => {
  it('shows pause for an active run and resume only for a paused run', () => {
    const actions = callbacks()
    const { rerender } = render(<RunControls runStatus="RUNNING" paused={false} {...actions} />)
    expect(screen.getByRole('button', { name: 'Pause' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Resume' })).not.toBeInTheDocument()

    rerender(<RunControls runStatus="RUNNING" paused {...actions} />)
    expect(screen.getByRole('button', { name: 'Resume' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Pause' })).not.toBeInTheDocument()
  })

  it.each([
    ['FAILED', ['Retry']],
    ['INTERRUPTED', ['Retry']],
    ['NEEDS_ATTENTION', ['Retry', 'Cancel']],
    ['PENDING', ['Cancel']],
    ['BLOCKED', ['Cancel', 'Skip']],
    ['READY', ['Cancel', 'Skip', 'Mark success']],
    ['RUNNING', ['Cancel']],
    ['SUCCESS', []],
    ['SKIPPED', []],
  ] as const)('applies the task visibility matrix for %s', (taskStatus, visible) => {
    const actions = callbacks()
    render(<RunControls runStatus="SUCCESS" paused={false} taskStatus={taskStatus} {...actions} />)
    for (const label of visible) expect(screen.getByRole('button', { name: label })).toBeInTheDocument()
    for (const label of ['Retry', 'Cancel', 'Skip', 'Mark success']) {
      if (!visible.includes(label as never)) expect(screen.queryByRole('button', { name: label })).not.toBeInTheDocument()
    }
    expect(screen.queryByRole('button', { name: 'Pause' })).not.toBeInTheDocument()
  })

  it('uses explicit callbacks and disables controls without a callback', async () => {
    const user = userEvent.setup()
    const onPause = vi.fn()
    render(<RunControls runStatus="RUNNING" paused={false} onPause={onPause} />)
    await user.click(screen.getByRole('button', { name: 'Pause' }))
    expect(onPause).toHaveBeenCalledOnce()
    expect(screen.getByRole('button', { name: 'Pause' })).not.toBeDisabled()
  })

  it('shows pending and error feedback for a run control', () => {
    const actions = callbacks()
    const { rerender } = render(<RunControls runStatus="RUNNING" paused={false} pendingAction="pause" {...actions} />)
    expect(screen.getByRole('button', { name: 'Pause…' })).toBeDisabled()
    rerender(<RunControls runStatus="RUNNING" paused={false} error="already paused" {...actions} />)
    expect(screen.getByRole('alert')).toHaveTextContent('already paused')
  })

  it.each(['FAILED', 'INTERRUPTED', 'NEEDS_ATTENTION'] as const)('invokes Retry explicitly for %s', async (taskStatus) => {
    const user = userEvent.setup()
    const onRetry = vi.fn()
    render(<RunControls runStatus="SUCCESS" paused={false} taskStatus={taskStatus} onRetry={onRetry} />)
    await user.click(screen.getByRole('button', { name: 'Retry' }))
    expect(onRetry).toHaveBeenCalledOnce()
  })
})
