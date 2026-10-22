import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { fixtureTaskRun } from '../../test/fixtures'
import TaskRunDrawer from './TaskRunDrawer'

const attemptApi = { attempts: vi.fn().mockResolvedValue([]) }

describe('TaskRunDrawer', () => {
  it('shows task metadata and closes on request', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    render(<TaskRunDrawer task={fixtureTaskRun} onClose={onClose} attemptApi={attemptApi} />)
    expect(screen.getByRole('heading', { name: 'Task A' })).toBeInTheDocument()
    expect(screen.getByText('RUNNING')).toBeInTheDocument()
    expect(screen.getByText('thread-1')).toBeInTheDocument()
    expect(screen.getByText('turn-1')).toBeInTheDocument()
    expect(screen.getByText(fixtureTaskRun.created_at)).toBeInTheDocument()
    expect(screen.getByText('These controls update durable workflow state. Cancel, Skip, and Mark success require confirmation.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Close task details' }))
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('renders missing optional execution IDs clearly', async () => {
    render(<TaskRunDrawer task={{ ...fixtureTaskRun, thread_id: null, turn_id: null }} onClose={vi.fn()} attemptApi={attemptApi} />)
    expect(screen.getAllByText('Not available')).toHaveLength(2)
    expect(await screen.findByText('No attempts recorded.')).toBeInTheDocument()
  })

  it('renders nothing without a selected task', () => {
    render(<TaskRunDrawer task={null} onClose={vi.fn()} />)
    expect(screen.queryByTestId('task-run-drawer')).not.toBeInTheDocument()
  })

  it.each(['FAILED', 'INTERRUPTED', 'NEEDS_ATTENTION'] as const)('shows Retry for %s only with an explicit callback', async (status) => {
    const onRetry = vi.fn()
    const user = userEvent.setup()
    render(<TaskRunDrawer task={{ ...fixtureTaskRun, status }} onClose={vi.fn()} onRetry={onRetry} attemptApi={attemptApi} />)
    await user.click(screen.getByRole('button', { name: 'Retry' }))
    expect(onRetry).toHaveBeenCalledOnce()
  })

  it('does not show Retry for a successful task', () => {
    render(<TaskRunDrawer task={{ ...fixtureTaskRun, status: 'SUCCESS' }} onClose={vi.fn()} onRetry={vi.fn()} attemptApi={attemptApi} />)
    expect(screen.queryByRole('button', { name: 'Retry' })).not.toBeInTheDocument()
  })

  it.each(['PENDING', 'BLOCKED', 'READY', 'STARTING', 'RUNNING', 'NEEDS_ATTENTION'] as const)('shows and invokes Cancel for %s', async (status) => {
    const onCancel = vi.fn()
    const user = userEvent.setup()
    render(<TaskRunDrawer task={{ ...fixtureTaskRun, status }} onClose={vi.fn()} onCancel={onCancel} attemptApi={attemptApi} />)
    await user.click(screen.getByRole('button', { name: 'Cancel' }))
    await user.click(screen.getByRole('button', { name: 'Confirm Cancel' }))
    expect(onCancel).toHaveBeenCalledOnce()
  })

  it('disables Cancel while a cancellation is pending', () => {
    render(
      <TaskRunDrawer
        task={{ ...fixtureTaskRun, status: 'RUNNING' }}
        onClose={vi.fn()}
        onCancel={vi.fn()}
        pendingAction="cancel"
        attemptApi={attemptApi}
      />,
    )
    expect(screen.getByRole('button', { name: 'Cancel…' })).toBeDisabled()
  })

  it.each(['BLOCKED', 'READY'] as const)('shows and invokes Skip for %s', async (status) => {
    const onSkip = vi.fn()
    const user = userEvent.setup()
    render(<TaskRunDrawer task={{ ...fixtureTaskRun, status }} onClose={vi.fn()} onSkip={onSkip} attemptApi={attemptApi} />)
    await user.click(screen.getByRole('button', { name: 'Skip' }))
    await user.click(screen.getByRole('button', { name: 'Confirm Skip' }))
    expect(onSkip).toHaveBeenCalledOnce()
  })

  it('shows and invokes Mark success only for READY', async () => {
    const onMarkSuccess = vi.fn()
    const user = userEvent.setup()
    render(<TaskRunDrawer task={{ ...fixtureTaskRun, status: 'READY' }} onClose={vi.fn()} onMarkSuccess={onMarkSuccess} attemptApi={attemptApi} />)
    await user.click(screen.getByRole('button', { name: 'Mark success' }))
    await user.click(screen.getByRole('button', { name: 'Confirm Mark success' }))
    expect(onMarkSuccess).toHaveBeenCalledOnce()
  })

  it('does not show Skip or Mark success for a running task', () => {
    render(<TaskRunDrawer task={fixtureTaskRun} onClose={vi.fn()} onSkip={vi.fn()} onMarkSuccess={vi.fn()} attemptApi={attemptApi} />)
    expect(screen.queryByRole('button', { name: 'Skip' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Mark success' })).not.toBeInTheDocument()
  })
})
