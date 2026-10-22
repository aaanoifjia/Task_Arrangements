import { useState } from 'react'
import type { WorkflowDefinition } from '../../api/types'
import { STARTER_WORKFLOWS } from '../../samples/workflows'

type SampleWorkflowPickerProps = {
  samples?: readonly WorkflowDefinition[]
  onSelect: (sample: WorkflowDefinition) => void
  onCancel: () => void
}

const topologyFor = (sample: WorkflowDefinition): string => {
  if (sample.id.includes('fork-join')) return 'Fork/join graph'
  if (sample.id.includes('continuation')) return 'Continuation chain'
  return 'Linear graph'
}

function SampleWorkflowPicker({ samples = STARTER_WORKFLOWS, onSelect, onCancel }: SampleWorkflowPickerProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const selected = samples.find((sample) => sample.id === selectedId)

  return (
    <section className="workflow-picker" role="dialog" aria-modal="true" aria-labelledby="sample-picker-heading">
      <div className="workflow-picker__header">
        <div>
          <h2 id="sample-picker-heading">Try a sample workflow</h2>
          <p>Choose a topology to preview before creating a new workflow.</p>
        </div>
        <button type="button" onClick={onCancel}>Cancel</button>
      </div>
      <fieldset>
        <legend className="sr-only">Sample workflows</legend>
        <div className="workflow-picker__options">
          {samples.map((sample) => (
            <label className="workflow-picker__option" key={sample.id}>
              <input
                type="radio"
                name="sample-workflow"
                value={sample.id}
                checked={selectedId === sample.id}
                onChange={() => setSelectedId(sample.id)}
              />
              <span>
                <strong>{sample.name}</strong>
                <span>{topologyFor(sample)}</span>
                <small>{sample.description}</small>
              </span>
            </label>
          ))}
        </div>
      </fieldset>
      <div className="workflow-picker__footer">
        <button type="button" onClick={() => selected && onSelect(selected)} disabled={!selected}>
          Use selected sample
        </button>
      </div>
    </section>
  )
}

export default SampleWorkflowPicker
