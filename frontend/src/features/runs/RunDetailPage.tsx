import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import type { RunDetail, TaskRunView } from '../../api/types'
import { createRunApi, type RunApi } from './api'
import './RunDetailPage.css'

export type RunDetailPageProps = { api?: RunApi }

function isNotFound(cause: unknown): boolean {
  if (!cause || typeof cause !== 'object') return false
  const error = cause as { status?: number; code?: string }
  return error.status === 404 || error.code === 'NOT_FOUND'
}

function RunDetailPage({ api }: RunDetailPageProps) {
  const { runId } = useParams<{ runId: string }>()
  const stableApi = useMemo(() => api ?? createRunApi(), [api])
  const [run, setRun] = useState<RunDetail | null>(null)
  const [tasks, setTasks] = useState<TaskRunView[]>([])
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    if (!runId) return () => { mounted = false }
    setLoading(true)
    setNotFound(false)
    setError(null)
    void Promise.all([stableApi.get(runId), stableApi.tasks(runId)]).then(([detail, taskSnapshot]) => {
      if (!mounted) return
      setRun(detail)
      setTasks(taskSnapshot)
    }).catch((cause: unknown) => {
      if (!mounted) return
      setRun(null)
      setTasks([])
      if (isNotFound(cause)) setNotFound(true)
      else setError(cause instanceof Error ? cause.message : 'Unable to load run.')
    }).finally(() => {
      if (mounted) setLoading(false)
    })
    return () => { mounted = false }
  }, [runId, stableApi])

  if (loading) return <p role="status">Loading run…</p>
  if (notFound) return <section aria-labelledby="run-not-found-heading"><h1 id="run-not-found-heading">Run not found</h1><p>The requested run does not exist.</p></section>
  if (error) return <section aria-labelledby="run-error-heading"><h1 id="run-error-heading">Unable to load run</h1><p role="alert">{error}</p></section>
  if (!run) return <p role="alert">Run data is unavailable.</p>

  return (
    <section aria-labelledby="run-detail-heading" className="run-detail">
      <div className="run-detail__header">
        <div>
          <h1 id="run-detail-heading">Run {run.id}</h1>
          <p>Workflow: {run.workflow_id}</p>
        </div>
        <strong data-testid="run-status">{run.status}</strong>
      </div>
      <dl className="run-detail__metadata">
        <div><dt>Run ID</dt><dd>{run.id}</dd></div>
        <div><dt>Workflow ID</dt><dd>{run.workflow_id}</dd></div>
        <div><dt>Created</dt><dd><time dateTime={run.created_at}>{run.created_at}</time></dd></div>
      </dl>
      <section aria-labelledby="run-tasks-heading">
        <h2 id="run-tasks-heading">Tasks</h2>
        {tasks.length === 0
          ? <p>No tasks recorded.</p>
          : <ul className="run-detail__tasks">
            {tasks.map((task) => (
              <li key={task.id}>
                <strong>{task.task_id}</strong>
                <span>{task.status}</span>
                {task.thread_id && <span>Thread: {task.thread_id}</span>}
              </li>
            ))}
          </ul>}
      </section>
    </section>
  )
}

export default RunDetailPage
