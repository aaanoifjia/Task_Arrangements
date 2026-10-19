import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../../api/http'
import type { RunApi } from './api'

export type StartRunButtonProps = {
  workflowId: string
  runApi: Pick<RunApi, 'start'>
  dirty: boolean
  hasBlockingIssues?: boolean
}

function errorMessage(cause: unknown): string {
  if (cause instanceof ApiError && cause.code === 'ACTIVE_RUN') {
    return 'A run is already active for this workflow.'
  }
  return cause instanceof Error ? cause.message : 'Unable to start workflow run.'
}

function StartRunButton({ workflowId, runApi, dirty, hasBlockingIssues = false }: StartRunButtonProps) {
  const navigate = useNavigate()
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const disabled = dirty || hasBlockingIssues || starting

  const start = async () => {
    if (disabled) return
    setStarting(true)
    setError(null)
    try {
      const result = await runApi.start(workflowId)
      navigate(`/runs/${encodeURIComponent(result.run_id)}`)
    } catch (cause) {
      setError(errorMessage(cause))
    } finally {
      setStarting(false)
    }
  }

  return (
    <div className="start-run">
      <button type="button" onClick={() => void start()} disabled={disabled}>
        {starting ? 'Starting…' : 'Start run'}
      </button>
      {dirty && <p>Save the workflow before starting a run.</p>}
      {hasBlockingIssues && <p>Fix validation issues before starting a run.</p>}
      {error && <p role="alert">{error}</p>}
    </div>
  )
}

export default StartRunButton
