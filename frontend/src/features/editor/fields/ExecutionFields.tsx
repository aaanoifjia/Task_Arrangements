import type { SandboxMode, TaskDefinition } from '../../../api/types'

export type ExecutionFieldsProps = {
  sandbox: SandboxMode
  approvalMode: TaskDefinition['approval_mode']
  onChange: (changes: Partial<Pick<TaskDefinition, 'sandbox' | 'approval_mode'>>) => void
}

const sandboxOptions: SandboxMode[] = ['read_only', 'workspace_write', 'full_access']

function ExecutionFields({ sandbox, approvalMode, onChange }: ExecutionFieldsProps) {
  return (
    <fieldset className="execution-fields">
      <legend>Execution permissions</legend>
      <label>
        Sandbox
        <select
          aria-label="Sandbox"
          value={sandbox}
          onChange={(event) => onChange({ sandbox: event.target.value as SandboxMode })}
        >
          {sandboxOptions.map((option) => <option key={option} value={option}>{option}</option>)}
        </select>
      </label>
      <label>
        Approval mode
        <input
          aria-label="Approval mode"
          value={approvalMode ?? ''}
          onChange={(event) => onChange({ approval_mode: event.target.value || null })}
        />
      </label>
    </fieldset>
  )
}

export default ExecutionFields
