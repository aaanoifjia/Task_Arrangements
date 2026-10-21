import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import type { RunSummary, TaskRunView } from '../../api/types'
import { createRunApi, type RunApi } from '../runs/api'
import './AttentionCenter.css'

type AttentionItem = { run: RunSummary; task: TaskRunView }

export type AttentionCenterProps = { api?: Pick<RunApi, 'list' | 'tasks'> }

function AttentionCenter({ api }: AttentionCenterProps) {
  const stableApi = useMemo(() => api ?? createRunApi(), [api])
  const [items, setItems] = useState<AttentionItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    setLoading(true)
    setError(null)
    void stableApi.list().then(async (runs) => {
      const tasksByRun = await Promise.all(runs.map(async (run) => ({
        run,
        tasks: await stableApi.tasks(run.id),
      })))
      if (!mounted) return
      setItems(tasksByRun.flatMap(({ run, tasks }) => tasks
        .filter((task) => task.status === 'NEEDS_ATTENTION')
        .map((task) => ({ run, task }))))
    }).catch((cause: unknown) => {
      if (!mounted) return
      setItems([])
      setError(cause instanceof Error ? cause.message : 'Unable to load attention items.')
    }).finally(() => {
      if (mounted) setLoading(false)
    })
    return () => { mounted = false }
  }, [stableApi])

  return (
    <aside className="attention-center" aria-labelledby="attention-center-heading">
      <div className="attention-center__header">
        <h2 id="attention-center-heading">Attention</h2>
        <span aria-label={`${items.length} tasks need attention`} data-testid="attention-count">{items.length}</span>
      </div>
      {loading && <p role="status">Loading attention items…</p>}
      {error && <p role="alert">{error}</p>}
      {!loading && !error && items.length === 0 && <p>No tasks need attention.</p>}
      {!loading && !error && items.length > 0 && (
        <ul className="attention-center__items">
          {items.map(({ run, task }) => (
            <li key={task.id}>
              <Link to={`/runs/${encodeURIComponent(run.id)}?task_id=${encodeURIComponent(task.task_id)}`}>
                <strong>{task.task_id}</strong>
                <span>Run {run.id}</span>
                <span>{task.status}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </aside>
  )
}

export default AttentionCenter
