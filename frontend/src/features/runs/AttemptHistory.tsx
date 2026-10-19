import { useEffect, useMemo, useState } from 'react'
import type { AttemptView } from '../../api/types'
import { createRunApi, type RunApi } from './api'

export type AttemptHistoryProps = {
  runId: string
  taskId: string
  api?: Pick<RunApi, 'attempts'>
}

function optionalValue(value: string | null): string {
  return value ?? 'Not available'
}

function AttemptHistory({ runId, taskId, api }: AttemptHistoryProps) {
  const stableApi = useMemo(() => api ?? createRunApi(), [api])
  const [attempts, setAttempts] = useState<AttemptView[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    setLoading(true)
    setError(null)
    void stableApi.attempts(runId, taskId).then((loaded) => {
      if (mounted) setAttempts(loaded)
    }).catch((cause: unknown) => {
      if (mounted) setError(cause instanceof Error ? cause.message : 'Unable to load attempts.')
    }).finally(() => {
      if (mounted) setLoading(false)
    })
    return () => { mounted = false }
  }, [runId, taskId, stableApi])

  return (
    <section aria-labelledby="attempt-history-heading" className="attempt-history">
      <h3 id="attempt-history-heading">Attempts</h3>
      {loading && <p role="status">Loading attempts…</p>}
      {error && <p role="alert">{error}</p>}
      {!loading && !error && attempts.length === 0 && <p>No attempts recorded.</p>}
      {!loading && !error && attempts.length > 0 && (
        <ol>
          {attempts.map((attempt) => (
            <li key={attempt.id}>
              <strong>{attempt.id}</strong>
              <span>Status: {attempt.status}</span>
              <span>Thread: {optionalValue(attempt.thread_id)}</span>
              <span>Turn: {optionalValue(attempt.turn_id)}</span>
              <time dateTime={attempt.created_at}>{attempt.created_at}</time>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}

export default AttemptHistory
