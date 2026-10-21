import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import ConfirmActionDialog from './ConfirmActionDialog'

describe('ConfirmActionDialog', () => {
  it('focuses the confirm action and closes on Escape', async () => {
    const user = userEvent.setup()
    const onCancel = vi.fn()
    render(<ConfirmActionDialog action="cancel" open onConfirm={vi.fn()} onCancel={onCancel} />)
    expect(screen.getByRole('button', { name: 'Confirm Cancel' })).toHaveFocus()
    await user.keyboard('{Escape}')
    expect(onCancel).toHaveBeenCalledOnce()
  })

  it('invokes the confirmed destructive action', async () => {
    const user = userEvent.setup()
    const onConfirm = vi.fn()
    render(<ConfirmActionDialog action="mark-success" open onConfirm={onConfirm} onCancel={vi.fn()} />)
    await user.click(screen.getByRole('button', { name: 'Confirm Mark success' }))
    expect(onConfirm).toHaveBeenCalledOnce()
  })

  it('renders nothing when closed', () => {
    render(<ConfirmActionDialog action="skip" open={false} onConfirm={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
