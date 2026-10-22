import { useState } from 'react'
import { createApiClient, type WorkflowExportResponse } from '../../api/client'

const sanitizeWorkflowFilename = (name: string): string => {
  const withoutControlCharacters = [...name].filter((character) => character.charCodeAt(0) >= 32).join('')
  const safe = withoutControlCharacters.normalize('NFKC')
    .replace(/[<>:"/\\|?*]/g, '-')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80)
  return `${safe || 'workflow'}.json`
}

type WorkflowExportButtonProps = {
  workflowId: string
  workflowName: string
  exporter?: (id: string) => Promise<WorkflowExportResponse>
}

function WorkflowExportButton({ workflowId, workflowName, exporter }: WorkflowExportButtonProps) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleExport = async () => {
    setBusy(true)
    setError(null)
    try {
      const payload = await (exporter ?? createApiClient().exportWorkflow)(workflowId)
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = sanitizeWorkflowFilename(workflowName)
      anchor.click()
      URL.revokeObjectURL(url)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to export workflow')
    } finally {
      setBusy(false)
    }
  }

  return (
    <span>
      <button type="button" onClick={() => void handleExport()} disabled={busy} aria-busy={busy}>
        {busy ? 'Exporting…' : 'Export JSON'}
      </button>
      {error && <span role="alert">{error}</span>}
    </span>
  )
}

export default WorkflowExportButton
