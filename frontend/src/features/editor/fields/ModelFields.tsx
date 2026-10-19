import type { TaskDefinition } from '../../../api/types'

export type ModelFieldsProps = {
  model: TaskDefinition['model']
  reasoningEffort: TaskDefinition['reasoning_effort']
  onChange: (changes: Partial<Pick<TaskDefinition, 'model' | 'reasoning_effort'>>) => void
}

function ModelFields({ model, reasoningEffort, onChange }: ModelFieldsProps) {
  return (
    <fieldset className="model-fields">
      <legend>Model configuration</legend>
      <label>
        Model
        <input
          aria-label="Model"
          value={model ?? ''}
          onChange={(event) => onChange({ model: event.target.value || null })}
        />
      </label>
      <label>
        Reasoning effort
        <input
          aria-label="Reasoning effort"
          value={reasoningEffort ?? ''}
          onChange={(event) => onChange({ reasoning_effort: event.target.value || null })}
        />
      </label>
    </fieldset>
  )
}

export default ModelFields
