import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import type { RunSummary } from '../../api/types'
import { createRunApi, type RunApi } from './api'
import './RunListPage.css'

export type RunListPageProps = { api?: RunApi }

function RunListPage({ api }: RunListPageProps) {
  const stableApi = useMemo(() => api ?? createRunApi(), [api])
  const [searchParams] = useSearchParams()
  const workflowFilter = searchParams.get('workflow_id')?.trim() ?? ''
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setRuns(await stableApi.list())
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to load runs.')
    } finally {
      setLoading(false)
    }
  }, [stableApi])

  useEffect(() => { void refresh() }, [refresh])

  const visibleRuns = workflowFilter
    ? runs.filter((run) => run.workflow_id === workflowFilter)
    : runs

  return (
    <section aria-labelledby="run-list-heading" className="run-list">
      <div className="run-list__header">
        <div>
          <h1 id="run-list-heading">Run history</h1>
          <p>{workflowFilter ? `Workflow: ${workflowFilter}` : 'Durable workflow runs.'}</p>
        </div>
        <button type="button" onClick={() => void refresh()} disabled={loading}>Refresh</button>
      </div>
      {loading && <p role="status">Loading runs…</p>}
      {error && <p role="alert">{error}</p>}
      {!loading && !error && visibleRuns.length === 0 && (
        <p>{workflowFilter ? 'No runs found for this workflow.' : 'No runs yet.'}</p>
      )}
      {!loading && !error && visibleRuns.length > 0 && (
        <ul className="run-list__items">
          {visibleRuns.map((run) => (
            <li key={run.id}>
              <Link to={`/runs/${encodeURIComponent(run.id)}`}>
                <strong>{run.id}</strong>
                <span>Workflow: {run.workflow_id}</span>
                <span>Status: {run.status}</span>
                <time dateTime={run.created_at}>{run.created_at}</time>
              </Link>
              <Link to={`/workflows/${encodeURIComponent(run.workflow_id)}`}>Open workflow</Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export default RunListPage
