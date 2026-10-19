import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { fixtureTaskRun } from '../../test/fixtures'
import TaskRunDrawer from './TaskRunDrawer'

describe('TaskRunDrawer', () => {
  it('shows task metadata and closes on request', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    render(<TaskRunDrawer task={fixtureTaskRun} onClose={onClose} />)
    expect(screen.getByRole('heading', { name: 'Task A' })).toBeInTheDocument()
    expect(screen.getByText('RUNNING')).toBeInTheDocument()
    expect(screen.getByText('thread-1')).toBeInTheDocument()
    expect(screen.getByText('turn-1')).toBeInTheDocument()
    expect(screen.getByText(fixtureTaskRun.created_at)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Close task details' }))
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('renders missing optional execution IDs clearly', () => {
    render(<TaskRunDrawer task={{ ...fixtureTaskRun, thread_id: null, turn_id: null }} onClose={vi.fn()} />)
    expect(screen.getAllByText('Not available')).toHaveLength(2)
  })

  it('renders nothing without a selected task', () => {
    render(<TaskRunDrawer task={null} onClose={vi.fn()} />)
    expect(screen.queryByTestId('task-run-drawer')).not.toBeInTheDocument()
  })
})
