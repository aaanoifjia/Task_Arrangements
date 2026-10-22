import { useState } from 'react'
import type { RunStatus, TaskStatus } from '../../api/types'
import ConfirmActionDialog, { type DestructiveAction } from './ConfirmActionDialog'
import './RunControls.css'

export type RunControlAction = 'pause' | 'resume' | 'retry' | 'cancel' | 'skip' | 'mark-success'

export type RunControlsProps = {
  runStatus: RunStatus
  paused: boolean
  taskStatus?: TaskStatus | null
  disabled?: boolean
  pendingAction?: RunControlAction | null
  error?: string | null
  onPause?: () => void
  onResume?: () => void
  onRetry?: () => void
  onCancel?: () => void
  onSkip?: () => void
  onMarkSuccess?: () => void
}

const activeRunStatuses = new Set<RunStatus>(['PENDING', 'READY', 'STARTING', 'RUNNING'])
const retryableTaskStatuses = new Set<TaskStatus>(['FAILED', 'INTERRUPTED', 'NEEDS_ATTENTION'])
const cancellableTaskStatuses = new Set<TaskStatus>([
  'PENDING', 'BLOCKED', 'READY', 'STARTING', 'RUNNING', 'NEEDS_ATTENTION',
])
const skippableTaskStatuses = new Set<TaskStatus>(['BLOCKED', 'READY'])

function ControlButton({
  action,
  label,
  help,
  disabled,
  pending,
  onClick,
}: {
  action: string
  label: string
  help: string
  disabled: boolean
  pending: boolean
  onClick?: () => void
}) {
  const helpId = `run-control-${action}-help`
  return (
    <div>
      <button
        type="button"
        data-testid={`run-control-${action}`}
        aria-describedby={helpId}
        disabled={disabled || pending || !onClick}
        onClick={onClick}
      >
        {pending ? `${label}…` : label}
      </button>
      <small id={helpId}>{help}</small>
    </div>
  )
}

function RunControls({
  runStatus,
  paused,
  taskStatus = null,
  disabled = false,
  pendingAction = null,
  error = null,
  onPause,
  onResume,
  onRetry,
  onCancel,
  onSkip,
  onMarkSuccess,
}: RunControlsProps) {
  const [confirmation, setConfirmation] = useState<DestructiveAction | null>(null)
  const canControlRun = activeRunStatuses.has(runStatus)
  const hasTask = taskStatus !== null
  const requestCancel = onCancel ? () => setConfirmation('cancel') : undefined
  const requestSkip = onSkip ? () => setConfirmation('skip') : undefined
  const requestMarkSuccess = onMarkSuccess ? () => setConfirmation('mark-success') : undefined
  const confirmAction = () => {
    const callback = confirmation === 'cancel' ? onCancel : confirmation === 'skip' ? onSkip : onMarkSuccess
    setConfirmation(null)
    callback?.()
  }

  return (
    <>
      <section className="run-controls" aria-labelledby="run-controls-heading" data-testid="run-controls">
        <h2 id="run-controls-heading">Controls</h2>
        {error && <p role="alert" className="run-controls__error">{error}</p>}
        <div className="run-controls__actions">
          {canControlRun && !paused && <ControlButton action="pause" label="Pause" help="Prevents new ready tasks from starting." disabled={disabled} pending={pendingAction === 'pause'} onClick={onPause} />}
          {canControlRun && paused && <ControlButton action="resume" label="Resume" help="Allows dependency-ready tasks to start again." disabled={disabled} pending={pendingAction === 'resume'} onClick={onResume} />}
          {hasTask && retryableTaskStatuses.has(taskStatus) && <ControlButton action="retry" label="Retry" help="Starts a new attempt for this task." disabled={disabled} pending={pendingAction === 'retry'} onClick={onRetry} />}
          {hasTask && cancellableTaskStatuses.has(taskStatus) && <ControlButton action="cancel" label="Cancel" help="Stops this task after confirmation." disabled={disabled} pending={pendingAction === 'cancel'} onClick={requestCancel} />}
          {hasTask && skippableTaskStatuses.has(taskStatus) && <ControlButton action="skip" label="Skip" help="Marks this task skipped; dependent tasks remain blocked." disabled={disabled} pending={pendingAction === 'skip'} onClick={requestSkip} />}
          {hasTask && taskStatus === 'READY' && <ControlButton action="mark-success" label="Mark success" help="Records success and may release dependent tasks." disabled={disabled} pending={pendingAction === 'mark-success'} onClick={requestMarkSuccess} />}
        </div>
      </section>
      <ConfirmActionDialog
        action={confirmation ?? 'cancel'}
        open={confirmation !== null}
        onConfirm={confirmAction}
        onCancel={() => setConfirmation(null)}
      />
    </>
  )
}

export default RunControls
