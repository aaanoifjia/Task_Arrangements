import { useEffect, useState } from 'react'
import type { WorkflowDefinition } from '../../api/types'
import './WorkflowMetadataPanel.css'

export type WorkflowMetadataChanges = Partial<Pick<WorkflowDefinition, 'name' | 'description'>>

export type WorkflowMetadataPanelProps = {
  workflowId: string
  name: string
  description: string | null
  onChange?: (changes: WorkflowMetadataChanges) => void
}

function WorkflowMetadataPanel({ workflowId, name, description, onChange }: WorkflowMetadataPanelProps) {
  const [draftName, setDraftName] = useState(name)
  const [draftDescription, setDraftDescription] = useState(description ?? '')
  const dirty = draftName !== name || draftDescription !== (description ?? '')

  useEffect(() => {
    setDraftName(name)
    setDraftDescription(description ?? '')
  }, [name, description])

  return (
    <section className="workflow-metadata-panel" aria-label="Workflow metadata">
      <div className="workflow-metadata-panel__header">
        <h2>Workflow details</h2>
        <span data-testid="metadata-dirty">{dirty ? 'Unsaved changes' : 'Saved'}</span>
      </div>
      <label>
        Workflow ID
        <input aria-label="Workflow ID" value={workflowId} readOnly />
      </label>
      <label>
        Workflow name
        <input
          aria-label="Workflow name"
          required
          value={draftName}
          onChange={(event) => {
            setDraftName(event.target.value)
            onChange?.({ name: event.target.value })
          }}
        />
      </label>
      <label>
        Description
        <textarea
          aria-label="Workflow description"
          rows={3}
          value={draftDescription}
          onChange={(event) => {
            setDraftDescription(event.target.value)
            onChange?.({ description: event.target.value || null })
          }}
        />
      </label>
    </section>
  )
}

export default WorkflowMetadataPanel
