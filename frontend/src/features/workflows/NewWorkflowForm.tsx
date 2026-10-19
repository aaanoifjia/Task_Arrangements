import { FormEvent, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { WorkflowDefinition } from '../../api/types'
import { createWorkflowApi } from './api'
import type { WorkflowApi } from './api'
import './NewWorkflowForm.css'

type NewWorkflowFormProps = { api?: WorkflowApi; onCreated?: () => void }

function NewWorkflowForm({ api, onCreated }: NewWorkflowFormProps) {
  const workflowApi = useMemo(() => api ?? createWorkflowApi(), [api])
  const navigate = useNavigate()
  const [id, setId] = useState('')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    if (!id.trim() || !name.trim()) {
      setError('Workflow id and name are required.')
      return
    }
    const workflow: WorkflowDefinition = {
      id: id.trim(), name: name.trim(), description: description.trim() || null,
      tasks: [], edges: [],
    }
    setError(null)
    setSaving(true)
    try {
      const created = await workflowApi.create(workflow)
      onCreated?.()
      navigate(`/workflows/${encodeURIComponent(created.workflow.id)}`)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to create workflow')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="new-workflow-form" onSubmit={(event) => void submit(event)}>
      <h2>New workflow</h2>
      <label>Workflow id<input value={id} onChange={(event) => setId(event.target.value)} /></label>
      <label>Name<input value={name} onChange={(event) => setName(event.target.value)} /></label>
      <label>Description<textarea value={description} onChange={(event) => setDescription(event.target.value)} /></label>
      {error && <p role="alert">{error}</p>}
      <button type="submit" disabled={saving}>{saving ? 'Saving…' : 'Create workflow'}</button>
    </form>
  )
}

export default NewWorkflowForm
