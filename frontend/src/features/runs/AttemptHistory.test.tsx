import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { AttemptView } from '../../api/types'
import type { RunApi } from './api'
import AttemptHistory from './AttemptHistory'

const attempts: AttemptView[] = [
  {
    id: 'attempt-1', task_run_id: 'task-a', status: 'FAILED', thread_id: 'thread-1', turn_id: 'turn-1',
    created_at: '2026-01-01T00:00:01Z',
  },
  {
    id: 'attempt-2', task_run_id: 'task-a', status: 'SUCCESS', thread_id: 'thread-2', turn_id: 'turn-2',
    created_at: '2026-01-01T00:00:02Z',
  },
]

function api(overrides: Partial<Pick<RunApi, 'attempts'>> = {}): Pick<RunApi, 'attempts'> {
  return { attempts: vi.fn().mockResolvedValue(attempts), ...overrides }
}

describe('AttemptHistory', () => {
  it('loads and preserves attempt API order', async () => {
    const attemptsApi = api()
    render(<AttemptHistory runId="run-1" taskId="A" api={attemptsApi} />)
    expect(screen.getByRole('status')).toHaveTextContent('Loading attempts')
    expect(await screen.findByText('attempt-1')).toBeInTheDocument()
    const items = screen.getAllByRole('listitem')
    expect(items[0]).toHaveTextContent('FAILED')
    expect(items[1]).toHaveTextContent('SUCCESS')
    expect(attemptsApi.attempts).toHaveBeenCalledWith('run-1', 'A')
  })

  it('renders empty and error states', async () => {
    const empty = api({ attempts: vi.fn().mockResolvedValue([]) })
    const { rerender } = render(<AttemptHistory runId="run-1" taskId="A" api={empty} />)
    expect(await screen.findByText('No attempts recorded.')).toBeInTheDocument()
    rerender(<AttemptHistory runId="run-1" taskId="A" api={api({ attempts: vi.fn().mockRejectedValue(new Error('offline')) })} />)
    expect(await screen.findByRole('alert')).toHaveTextContent('offline')
  })
})
