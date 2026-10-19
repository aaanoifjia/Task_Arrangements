import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import type { EventView, RunDetail, TaskRunView } from '../../api/types'
import { createRunApi, type RunApi } from './api'
import EventLog from './EventLog'
import RunSummaryPanel from './RunSummaryPanel'
import RunGraph from './RunGraph'
import { useRunStream, type UseRunStreamOptions } from './useRunStream'
import './RunDetailPage.css'

export type RunDetailPageProps = { api?: RunApi; streamOptions?: UseRunStreamOptions }

function isNotFound(cause: unknown): boolean {
  if (!cause || typeof cause !== 'object') return false
  const error = cause as { status?: number; code?: string }
  return error.status === 404 || error.code === 'NOT_FOUND'
}

function RunDetailPage({ api, streamOptions }: RunDetailPageProps) {
  const { runId } = useParams<{ runId: string }>()
  const stableApi = useMemo(() => api ?? createRunApi(), [api])
  const stream = useRunStream(runId, streamOptions)
  const [run, setRun] = useState<RunDetail | null>(null)
  const [tasks, setTasks] = useState<TaskRunView[]>([])
  const [events, setEvents] = useState<EventView[]>([])
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setEvents([])
  }, [runId])

  useEffect(() => {
    const event = stream.latestEvent
    if (!event) return
    setEvents((current) => current.some((item) => item.id === event.id) ? current : [...current, event])
  }, [stream.latestEvent])

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
  const visibleTasks = stream.hasSnapshot ? stream.tasks : tasks

  return (
    <section aria-labelledby="run-detail-heading" className="run-detail">
      <div className="run-detail__header">
        <div>
          <h1 id="run-detail-heading">Run {run.id}</h1>
          <p>Workflow: {run.workflow_id}</p>
        </div>
        <strong data-testid="run-status">{run.status}</strong>
      </div>
      <nav aria-label="Run navigation">
        <Link to={`/workflows/${encodeURIComponent(run.workflow_id)}`}>Back to workflow</Link>
        <Link to={`/runs?workflow_id=${encodeURIComponent(run.workflow_id)}`}>Workflow runs</Link>
      </nav>
      <dl className="run-detail__metadata">
        <div><dt>Run ID</dt><dd>{run.id}</dd></div>
        <div><dt>Workflow ID</dt><dd>{run.workflow_id}</dd></div>
        <div><dt>Created</dt><dd><time dateTime={run.created_at}>{run.created_at}</time></dd></div>
      </dl>
      <RunSummaryPanel runStatus={run.status} tasks={visibleTasks} />
      <section aria-labelledby="run-graph-heading">
        <h2 id="run-graph-heading">Snapshot graph</h2>
        <RunGraph snapshot={run.snapshot} taskRuns={visibleTasks} attemptApi={stableApi} />
      </section>
      <section aria-labelledby="run-tasks-heading">
        <h2 id="run-tasks-heading">Tasks</h2>
        {visibleTasks.length === 0
          ? <p>No tasks recorded.</p>
          : <ul className="run-detail__tasks">
            {visibleTasks.map((task) => (
              <li key={task.id}>
                <strong>{task.task_id}</strong>
                <span>{task.status}</span>
                {task.thread_id && <span>Thread: {task.thread_id}</span>}
              </li>
            ))}
          </ul>}
      </section>
      <EventLog events={events} />
    </section>
  )
}

export default RunDetailPage
