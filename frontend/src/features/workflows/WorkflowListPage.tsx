import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import type { WorkflowSummary } from '../../api/types'
import { createWorkflowApi } from './api'
import type { WorkflowApi } from './api'
import NewWorkflowForm from './NewWorkflowForm'
import './WorkflowListPage.css'
import './workflows.css'

type WorkflowListPageProps = { api?: WorkflowApi; onTrySample?: () => void }

function WorkflowListPage({ api, onTrySample }: WorkflowListPageProps) {
  const stableApi = useMemo(() => api ?? createWorkflowApi(), [api])
  const [showCreate, setShowCreate] = useState(false)
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setWorkflows(await stableApi.list())
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to load workflows')
    } finally {
      setLoading(false)
    }
  }, [stableApi])

  useEffect(() => { void refresh() }, [refresh])

  return (
    <section aria-labelledby="workflow-list-heading" className="workflow-list">
      <div className="workflow-list__header">
        <div>
          <h1 id="workflow-list-heading">Codex Flow</h1>
          <p>Workflows</p>
        </div>
        <div>
          <button type="button" onClick={() => setShowCreate((visible) => !visible)}>New workflow</button>
          <button type="button" onClick={() => void refresh()} disabled={loading}>Refresh</button>
        </div>
      </div>
      {showCreate && <NewWorkflowForm api={stableApi} onCreated={() => setShowCreate(false)} />}
      {loading && <p role="status">Loading workflows…</p>}
      {error && <p role="alert">{error}</p>}
      {!loading && !error && workflows.length === 0 && (
        <div className="workflow-list__empty" aria-labelledby="workflow-empty-heading">
          <h2 id="workflow-empty-heading">Start your first workflow</h2>
          <p>No workflows yet. Create one from scratch or try a safe sample.</p>
          <div className="workflow-list__empty-actions">
            <button type="button" onClick={() => setShowCreate(true)}>Create workflow</button>
            <button type="button" onClick={() => onTrySample?.()}>Try a sample</button>
          </div>
        </div>
      )}
      {!loading && !error && workflows.length > 0 && (
        <ul className="workflow-list__items">
          {workflows.map((workflow) => (
            <li key={workflow.id}>
              <Link to={`/workflows/${encodeURIComponent(workflow.id)}`}>
                <strong>{workflow.name}</strong><span>{workflow.id}</span>
              </Link>
              <Link to={`/runs?workflow_id=${encodeURIComponent(workflow.id)}`}>View runs</Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export default WorkflowListPage
