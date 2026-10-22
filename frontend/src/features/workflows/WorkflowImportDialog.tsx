import { useState } from 'react'
import type { WorkflowDetail, WorkflowImportRequest } from '../../api/types'

type WorkflowImportDialogProps = {
  importer: (request: WorkflowImportRequest) => Promise<WorkflowDetail>
  onImported: (detail: WorkflowDetail) => void
  onCancel: () => void
}

function readFileText(file: File): Promise<string> {
  if (typeof file.text === 'function') return file.text()
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result ?? ''))
    reader.onerror = () => reject(new Error('Unable to read workflow file'))
    reader.readAsText(file)
  })
}

function WorkflowImportDialog({ importer, onImported, onCancel }: WorkflowImportDialogProps) {
  const [file, setFile] = useState<File | null>(null)
  const [replacementId, setReplacementId] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const importFile = async () => {
    if (!file) {
      setError('Choose a workflow JSON file first.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      const parsed: unknown = JSON.parse(await readFileText(file))
      if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
        throw new Error('Workflow export must be a JSON object.')
      }
      const request = {
        ...parsed,
        ...(replacementId.trim() ? { replacement_id: replacementId.trim() } : {}),
      } as WorkflowImportRequest
      onImported(await importer(request))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to import workflow')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="workflow-import" role="dialog" aria-modal="true" aria-labelledby="workflow-import-heading">
      <div className="workflow-import__header">
        <h2 id="workflow-import-heading">Import workflow</h2>
        <button type="button" onClick={onCancel} disabled={busy}>Cancel</button>
      </div>
      <label>
        Workflow JSON file
        <input
          type="file"
          accept=".json,application/json"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
      </label>
      <label>
        Replacement ID (optional)
        <input
          value={replacementId}
          onChange={(event) => setReplacementId(event.target.value)}
          placeholder="Only needed for an existing workflow ID"
        />
      </label>
      {file && <p role="status">Selected: {file.name}</p>}
      {error && <p role="alert">{error}</p>}
      <div className="workflow-import__footer">
        <button type="button" onClick={() => void importFile()} disabled={busy}>
          {busy ? 'Importing…' : 'Import workflow'}
        </button>
      </div>
    </div>
  )
}

export default WorkflowImportDialog
