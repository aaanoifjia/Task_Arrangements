import { useEffect, useRef } from 'react'
import './ConfirmActionDialog.css'

export type DestructiveAction = 'cancel' | 'skip' | 'mark-success'

export type ConfirmActionDialogProps = {
  action: DestructiveAction
  open: boolean
  onConfirm: () => void
  onCancel: () => void
}

const labels: Record<DestructiveAction, string> = {
  cancel: 'Cancel',
  skip: 'Skip',
  'mark-success': 'Mark success',
}

function ConfirmActionDialog({ action, open, onConfirm, onCancel }: ConfirmActionDialogProps) {
  const confirmRef = useRef<HTMLButtonElement>(null)
  const label = labels[action]

  useEffect(() => {
    if (!open) return
    confirmRef.current?.focus()
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onCancel()
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [onCancel, open])

  if (!open) return null
  return (
    <div className="confirm-action-dialog__backdrop">
      <div
        className="confirm-action-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-action-dialog-heading"
      >
        <h2 id="confirm-action-dialog-heading">Confirm {label}</h2>
        <p>This action changes the durable task state. Continue?</p>
        <div className="confirm-action-dialog__actions">
          <button type="button" onClick={onCancel}>Keep task</button>
          <button type="button" ref={confirmRef} onClick={onConfirm}>Confirm {label}</button>
        </div>
      </div>
    </div>
  )
}

export default ConfirmActionDialog
