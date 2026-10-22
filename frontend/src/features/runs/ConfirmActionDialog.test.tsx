import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
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

  it('restores focus to the triggering control after cancellation', async () => {
    const user = userEvent.setup()
    function Harness() {
      const [open, setOpen] = useState(false)
      return (
        <>
          <button type="button" onClick={() => setOpen(true)}>Open confirmation</button>
          <ConfirmActionDialog action="skip" open={open} onConfirm={() => setOpen(false)} onCancel={() => setOpen(false)} />
        </>
      )
    }
    render(<Harness />)

    const trigger = screen.getByRole('button', { name: 'Open confirmation' })
    await user.click(trigger)
    expect(screen.getByRole('button', { name: 'Confirm Skip' })).toHaveFocus()
    await user.click(screen.getByRole('button', { name: 'Keep task' }))
    expect(trigger).toHaveFocus()
  })
})
