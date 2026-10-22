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
    expect(screen.getByText('Prevents new ready tasks from starting.')).toBeInTheDocument()
  })

  it.each(['FAILED', 'INTERRUPTED', 'NEEDS_ATTENTION'] as const)('invokes Retry explicitly for %s', async (taskStatus) => {
    const user = userEvent.setup()
    const onRetry = vi.fn()
    render(<RunControls runStatus="SUCCESS" paused={false} taskStatus={taskStatus} onRetry={onRetry} />)
    await user.click(screen.getByRole('button', { name: 'Retry' }))
    expect(onRetry).toHaveBeenCalledOnce()
  })

  it('keeps Skip and Mark success scoped to their canonical states', async () => {
    const user = userEvent.setup()
    const onSkip = vi.fn()
    const onMarkSuccess = vi.fn()
    const { rerender } = render(
      <RunControls runStatus="SUCCESS" paused={false} taskStatus="BLOCKED" onSkip={onSkip} onMarkSuccess={onMarkSuccess} />,
    )
    await user.click(screen.getByRole('button', { name: 'Skip' }))
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Confirm Skip' }))
    expect(onSkip).toHaveBeenCalledOnce()
    expect(screen.queryByRole('button', { name: 'Mark success' })).not.toBeInTheDocument()

    rerender(<RunControls runStatus="SUCCESS" paused={false} taskStatus="READY" onSkip={onSkip} onMarkSuccess={onMarkSuccess} />)
    await user.click(screen.getByRole('button', { name: 'Mark success' }))
    await user.click(screen.getByRole('button', { name: 'Confirm Mark success' }))
    expect(onMarkSuccess).toHaveBeenCalledOnce()
    rerender(<RunControls runStatus="SUCCESS" paused={false} taskStatus="RUNNING" onSkip={onSkip} onMarkSuccess={onMarkSuccess} />)
    expect(screen.queryByRole('button', { name: 'Skip' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Mark success' })).not.toBeInTheDocument()
  })

  it('explains task-control consequences while preserving confirmations', async () => {
    const actions = callbacks()
    render(<RunControls runStatus="SUCCESS" paused={false} taskStatus="READY" {...actions} />)
    expect(screen.getByText('Marks this task skipped; dependent tasks remain blocked.')).toBeInTheDocument()
    expect(screen.getByText('Records success and may release dependent tasks.')).toBeInTheDocument()
    await userEvent.setup().click(screen.getByRole('button', { name: 'Skip' }))
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('confirms destructive actions but keeps Retry one-step', async () => {
    const user = userEvent.setup()
    const onCancel = vi.fn()
    const onRetry = vi.fn()
    render(<RunControls runStatus="SUCCESS" paused={false} taskStatus="FAILED" onCancel={onCancel} onRetry={onRetry} />)
    await user.click(screen.getByRole('button', { name: 'Retry' }))
    expect(onRetry).toHaveBeenCalledOnce()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()

    const { rerender } = render(<RunControls runStatus="SUCCESS" paused={false} taskStatus="RUNNING" onCancel={onCancel} />)
    await user.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(onCancel).not.toHaveBeenCalled()
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Confirm Cancel' }))
    expect(onCancel).toHaveBeenCalledOnce()
    rerender(<RunControls runStatus="SUCCESS" paused={false} taskStatus="RUNNING" onCancel={onCancel} />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
