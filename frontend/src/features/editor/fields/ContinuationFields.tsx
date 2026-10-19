import type { ExecutionMode, TaskDefinition } from '../../../api/types'

export type ContinuationFieldsProps = {
  taskId: string
  executionMode: ExecutionMode
  continueFromTaskId: string | null
  availableTaskIds: string[]
  onChange: (changes: Partial<Pick<TaskDefinition, 'execution_mode' | 'continue_from_task_id'>>) => void
}

function ContinuationFields({
  taskId,
  executionMode,
  continueFromTaskId,
  availableTaskIds,
  onChange,
}: ContinuationFieldsProps) {
  const sourceOptions = availableTaskIds.filter((id) => id !== taskId)
  const hasValidSource = continueFromTaskId !== null && sourceOptions.includes(continueFromTaskId)

  return (
    <fieldset className="continuation-fields">
      <legend>Thread execution</legend>
      <label>
        Execution mode
        <select
          aria-label="Execution mode"
          value={executionMode}
          onChange={(event) => {
            const mode = event.target.value as ExecutionMode
            onChange(mode === 'NEW_THREAD'
              ? { execution_mode: mode, continue_from_task_id: null }
              : { execution_mode: mode, continue_from_task_id: hasValidSource ? continueFromTaskId : null })
          }}
        >
          <option value="NEW_THREAD">NEW_THREAD</option>
          <option value="CONTINUE_THREAD">CONTINUE_THREAD</option>
        </select>
      </label>
      <label>
        Continue from task
        <select
          aria-label="Continue from task"
          value={hasValidSource ? continueFromTaskId : ''}
          disabled={executionMode === 'NEW_THREAD'}
          onChange={(event) => onChange({ continue_from_task_id: event.target.value || null })}
        >
          <option value="">Select a source task</option>
          {sourceOptions.map((id) => <option key={id} value={id}>{id}</option>)}
        </select>
      </label>
      {executionMode === 'CONTINUE_THREAD' && !hasValidSource && (
        <p role="alert">CONTINUE_THREAD requires a source task other than itself.</p>
      )}
    </fieldset>
  )
}

export default ContinuationFields
