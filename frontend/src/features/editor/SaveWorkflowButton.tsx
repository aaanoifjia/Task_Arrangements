import { useState } from 'react'
import type { WorkflowDefinition } from '../../api/types'
import type { WorkflowApi } from '../workflows/api'

export type SaveWorkflowButtonProps = {
  workflowId: string
  workflow: WorkflowDefinition
  workflowApi: Pick<WorkflowApi, 'update'>
  dirty: boolean
  hasBlockingIssues?: boolean
  onSaved?: () => void
}

function SaveWorkflowButton({
  workflowId,
  workflow,
  workflowApi,
  dirty,
  hasBlockingIssues = false,
  onSaved,
}: SaveWorkflowButtonProps) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const save = async () => {
    if (!dirty || hasBlockingIssues || saving) return
    setSaving(true)
    setError(null)
    try {
      await workflowApi.update(workflowId, workflow)
      onSaved?.()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to save workflow.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="save-workflow">
      <button type="button" onClick={() => void save()} disabled={!dirty || hasBlockingIssues || saving}>
        {saving ? 'Saving…' : 'Save workflow'}
      </button>
      {error && <p role="alert">{error}</p>}
    </div>
  )
}

export default SaveWorkflowButton
