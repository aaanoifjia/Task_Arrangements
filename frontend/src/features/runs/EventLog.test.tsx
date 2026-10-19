import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { EventView } from '../../api/types'
import EventLog from './EventLog'

const events: EventView[] = [
  {
    id: 'event-1', workflow_run_id: 'run-1', task_run_id: 'task-a', attempt_id: 'attempt-a',
    event_type: 'TURN_STARTED', payload: { sequence: 1 }, created_at: '2026-01-01T00:00:01Z',
  },
  {
    id: 'event-2', workflow_run_id: 'run-1', task_run_id: 'task-a', attempt_id: 'attempt-a',
    event_type: 'TURN_COMPLETED', payload: { status: 'completed', output: 'ok' }, created_at: '2026-01-01T00:00:02Z',
  },
]

describe('EventLog', () => {
  it('preserves arrival order and renders references and JSON payloads', () => {
    render(<EventLog events={events} />)
    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(2)
    expect(within(items[0]!).getByText('TURN_STARTED')).toBeInTheDocument()
    expect(within(items[1]!).getByText('TURN_COMPLETED')).toBeInTheDocument()
    expect(within(items[0]!).getByText('Task: task-a')).toBeInTheDocument()
    expect(within(items[0]!).getByText('Attempt: attempt-a')).toBeInTheDocument()
    expect(within(items[1]!).getByText(/"status": "completed"/)).toBeInTheDocument()
  })

  it('shows an empty state when no events have arrived', () => {
    render(<EventLog events={[]} />)
    expect(screen.getByText('No events recorded.')).toBeInTheDocument()
  })
})
