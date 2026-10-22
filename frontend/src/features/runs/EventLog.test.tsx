import { render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
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
  {
    id: 'event-3', workflow_run_id: 'run-1', task_run_id: 'task-b', attempt_id: 'attempt-b',
    event_type: 'TOOL_COMPLETED', payload: { status: 'completed' }, created_at: '2026-01-01T00:00:03Z',
  },
]

describe('EventLog', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: undefined })
  })

  it('preserves arrival order and renders references and JSON payloads', () => {
    render(<EventLog events={events} />)
    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(3)
    expect(within(items[0]!).getByText('TURN_STARTED')).toBeInTheDocument()
    expect(within(items[1]!).getByText('TURN_COMPLETED')).toBeInTheDocument()
    expect(within(items[2]!).getByText('TOOL_COMPLETED')).toBeInTheDocument()
    expect(within(items[0]!).getByText('Task: task-a')).toBeInTheDocument()
    expect(within(items[0]!).getByText('Attempt: attempt-a')).toBeInTheDocument()
    expect(within(items[1]!).getByText(/"status": "completed"/)).toBeInTheDocument()
  })

  it('shows an empty state when no events have arrived', () => {
    render(<EventLog events={[]} />)
    expect(screen.getByText('No events recorded.')).toBeInTheDocument()
  })

  it('filters by event type and task text, preserves order, and clears filters', async () => {
    const user = userEvent.setup()
    render(<EventLog events={events} />)

    await user.selectOptions(screen.getByLabelText('Event type'), 'TURN_COMPLETED')
    const completedItems = screen.getAllByRole('listitem')
    expect(completedItems).toHaveLength(1)
    expect(within(completedItems[0]!).getByText('TURN_COMPLETED')).toBeInTheDocument()
    await user.selectOptions(screen.getByLabelText('Event type'), '')
    await user.type(screen.getByLabelText('Task text'), 'task-a')
    const filtered = screen.getAllByRole('listitem')
    expect(filtered).toHaveLength(2)
    expect(within(filtered[0]!).getByText('TURN_STARTED')).toBeInTheDocument()
    expect(within(filtered[1]!).getByText('TURN_COMPLETED')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Clear filters' }))
    expect(screen.getAllByRole('listitem')).toHaveLength(3)
  })

  it('copies only safe event metadata and reports clipboard success', async () => {
    const user = userEvent.setup()
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } })
    render(<EventLog events={events} />)

    await user.click(within(screen.getAllByRole('listitem')[0]!).getByRole('button', { name: 'Copy details' }))

    expect(writeText).toHaveBeenCalledWith(expect.stringContaining('Event ID: event-1'))
    const copied = writeText.mock.calls[0]?.[0] as string
    expect(copied).toContain('Event type: TURN_STARTED')
    expect(copied).toContain('Task: task-a')
    expect(copied).not.toMatch(/token|prompt|payload/i)
    expect(screen.getByRole('status')).toHaveTextContent('Copied safe event details.')
  })

  it('shows safe details when the clipboard API is unavailable', async () => {
    const user = userEvent.setup()
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: undefined })
    render(<EventLog events={events} />)

    await user.click(within(screen.getAllByRole('listitem')[1]!).getByRole('button', { name: 'Copy details' }))

    expect(screen.getByRole('status')).toHaveTextContent('Clipboard unavailable.')
    expect(screen.getByRole('status')).toHaveTextContent('Event ID: event-2')
    expect(screen.getByRole('status')).not.toHaveTextContent('payload')
  })
})
