import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import type { EventView, RunDetail, TaskRunView } from '../../api/types'
import { createRunApi, type RunApi } from './api'
import EventLog from './EventLog'
import RunSummaryPanel from './RunSummaryPanel'
import RunGraph from './RunGraph'
import RunControls, { type RunControlAction } from './RunControls'
import { useRunStream, type UseRunStreamOptions } from './useRunStream'
import './RunDetailPage.css'

export type RunDetailPageProps = { api?: RunApi; streamOptions?: UseRunStreamOptions }

function isNotFound(cause: unknown): boolean {
  if (!cause || typeof cause !== 'object') return false
  const error = cause as { status?: number; code?: string }
  return error.status === 404 || error.code === 'NOT_FOUND'
}

function isConflict(cause: unknown): boolean {
  if (!cause || typeof cause !== 'object') return false
  const error = cause as { status?: number; code?: string }
  return error.status === 409 || error.code === 'CONFLICT'
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
  const [paused, setPaused] = useState(false)
  const [pendingControl, setPendingControl] = useState<RunControlAction | null>(null)
  const [controlError, setControlError] = useState<string | null>(null)
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)

  useEffect(() => {
    setEvents([])
    setPaused(false)
    setControlError(null)
  }, [runId])

  useEffect(() => {
    const event = stream.latestEvent
    if (!event) return
    setEvents((current) => current.some((item) => item.id === event.id) ? current : [...current, event])
  }, [stream.latestEvent])

  const refreshRun = useCallback(async () => {
    if (!runId) return
    const [detail, taskSnapshot] = await Promise.all([stableApi.get(runId), stableApi.tasks(runId)])
    setRun(detail)
    setTasks(taskSnapshot)
  }, [runId, stableApi])

  useEffect(() => {
    let mounted = true
    if (!runId) return () => { mounted = false }
    setLoading(true)
    setNotFound(false)
    setError(null)
    void Promise.all([stableApi.get(runId), stableApi.tasks(runId), stableApi.events?.(runId) ?? Promise.resolve([])]).then(([detail, taskSnapshot, persistedEvents]) => {
      if (!mounted) return
      setRun(detail)
      setTasks(taskSnapshot)
      setEvents(persistedEvents)
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

  useEffect(() => {
    if (!stream.latestEventId) return
    void refreshRun().catch(() => undefined)
  }, [refreshRun, stream.latestEventId])

  const applyRunControl = useCallback(async (action: 'pause' | 'resume') => {
    if (!runId) return
    const operation = action === 'pause' ? stableApi.pause : stableApi.resume
    if (!operation) return
    setPendingControl(action)
    setControlError(null)
    try {
      const result = await operation(runId)
      if (!result.accepted) throw new Error(result.message ?? `Unable to ${action} run.`)
      setPaused(action === 'pause')
      await refreshRun()
    } catch (cause: unknown) {
      if (isConflict(cause)) {
        await refreshRun().catch(() => undefined)
      }
      setControlError(cause instanceof Error ? cause.message : `Unable to ${action} run.`)
    } finally {
      setPendingControl(null)
    }
  }, [refreshRun, runId, stableApi])

  const applyTaskControl = useCallback(async (action: Exclude<RunControlAction, 'pause' | 'resume'>) => {
    if (!runId || !selectedTaskId) return
    const operation = action === 'retry'
      ? stableApi.retry
      : action === 'cancel'
        ? stableApi.cancel
        : action === 'skip'
          ? stableApi.skip
          : stableApi.markSuccess
    if (!operation) return
    setPendingControl(action)
    setControlError(null)
    try {
      const result = await operation(runId, selectedTaskId)
      if (!result.accepted) throw new Error(result.message ?? `Unable to ${action} task.`)
      await refreshRun()
    } catch (cause: unknown) {
      if (isConflict(cause)) await refreshRun().catch(() => undefined)
      setControlError(cause instanceof Error ? cause.message : `Unable to ${action} task.`)
    } finally {
      setPendingControl(null)
    }
  }, [refreshRun, runId, selectedTaskId, stableApi])

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
      <RunControls
        runStatus={run.status}
        paused={paused}
        disabled={pendingControl !== null}
        pendingAction={pendingControl}
        error={controlError}
        onPause={stableApi.pause ? () => { void applyRunControl('pause') } : undefined}
        onResume={stableApi.resume ? () => { void applyRunControl('resume') } : undefined}
      />
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
        <RunGraph
          snapshot={run.snapshot}
          taskRuns={visibleTasks}
          attemptApi={stableApi}
          onRetry={() => { void applyTaskControl('retry') }}
          onCancel={() => { void applyTaskControl('cancel') }}
          onSkip={() => { void applyTaskControl('skip') }}
          onMarkSuccess={() => { void applyTaskControl('mark-success') }}
          pendingAction={pendingControl}
          selectedTaskId={selectedTaskId}
          onSelectTask={setSelectedTaskId}
        />
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
                <button type="button" onClick={() => setSelectedTaskId(task.task_id)}>View details</button>
              </li>
            ))}
          </ul>}
      </section>
      <EventLog events={events} />
    </section>
  )
}

export default RunDetailPage
