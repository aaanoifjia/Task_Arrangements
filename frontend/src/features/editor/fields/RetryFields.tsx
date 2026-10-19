import { useState } from 'react'
import type { RetryPolicy, TaskDefinition } from '../../../api/types'

export type RetryFieldsProps = {
  timeoutSeconds: TaskDefinition['timeout_seconds']
  retryPolicy: RetryPolicy
  onChange: (changes: Partial<Pick<TaskDefinition, 'timeout_seconds' | 'retry_policy'>>) => void
}

function positiveInteger(value: string): number | null {
  const parsed = Number(value)
  return Number.isInteger(parsed) && parsed >= 1 ? parsed : null
}

function RetryFields({ timeoutSeconds, retryPolicy, onChange }: RetryFieldsProps) {
  const [error, setError] = useState<string | null>(null)
  const changeTimeout = (value: string) => {
    if (value === '') {
      setError(null)
      onChange({ timeout_seconds: null })
      return
    }
    const parsed = positiveInteger(value)
    if (parsed === null) {
      setError('Timeout must be a positive integer.')
      return
    }
    setError(null)
    onChange({ timeout_seconds: parsed })
  }
  const changeMaxAttempts = (value: string) => {
    const parsed = positiveInteger(value)
    if (parsed === null) {
      setError('Maximum attempts must be at least 1.')
      return
    }
    setError(null)
    onChange({ retry_policy: { max_attempts: parsed } })
  }

  return (
    <fieldset className="retry-fields">
      <legend>Timeout and retry</legend>
      <label>
        Timeout seconds
        <input
          aria-label="Timeout seconds"
          type="number"
          min="1"
          step="1"
          value={timeoutSeconds ?? ''}
          onChange={(event) => changeTimeout(event.target.value)}
        />
      </label>
      <label>
        Maximum attempts
        <input
          aria-label="Maximum attempts"
          type="number"
          min="1"
          step="1"
          value={retryPolicy.max_attempts}
          onChange={(event) => changeMaxAttempts(event.target.value)}
        />
      </label>
      {error && <p role="alert">{error}</p>}
    </fieldset>
  )
}

export default RetryFields
