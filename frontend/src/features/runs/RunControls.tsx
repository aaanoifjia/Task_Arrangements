import type { RunStatus, TaskStatus } from '../../api/types'
import './RunControls.css'

export type RunControlsProps = {
  runStatus: RunStatus
  paused: boolean
  taskStatus?: TaskStatus | null
  disabled?: boolean
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
  disabled,
  onClick,
}: {
  action: string
  label: string
  disabled: boolean
  onClick?: () => void
}) {
  return <button type="button" data-testid={`run-control-${action}`} disabled={disabled || !onClick} onClick={onClick}>{label}</button>
}

function RunControls({
  runStatus,
  paused,
  taskStatus = null,
  disabled = false,
  onPause,
  onResume,
  onRetry,
  onCancel,
  onSkip,
  onMarkSuccess,
}: RunControlsProps) {
  const canControlRun = activeRunStatuses.has(runStatus)
  const hasTask = taskStatus !== null

  return (
    <section className="run-controls" aria-labelledby="run-controls-heading" data-testid="run-controls">
      <h2 id="run-controls-heading">Controls</h2>
      <div className="run-controls__actions">
        {canControlRun && !paused && <ControlButton action="pause" label="Pause" disabled={disabled} onClick={onPause} />}
        {canControlRun && paused && <ControlButton action="resume" label="Resume" disabled={disabled} onClick={onResume} />}
        {hasTask && retryableTaskStatuses.has(taskStatus) && <ControlButton action="retry" label="Retry" disabled={disabled} onClick={onRetry} />}
        {hasTask && cancellableTaskStatuses.has(taskStatus) && <ControlButton action="cancel" label="Cancel" disabled={disabled} onClick={onCancel} />}
        {hasTask && skippableTaskStatuses.has(taskStatus) && <ControlButton action="skip" label="Skip" disabled={disabled} onClick={onSkip} />}
        {hasTask && taskStatus === 'READY' && <ControlButton action="mark-success" label="Mark success" disabled={disabled} onClick={onMarkSuccess} />}
      </div>
    </section>
  )
}

export default RunControls
