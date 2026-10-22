import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import type { EventView, RunSummary } from '../../api/types'
import EventLog from './EventLog'
import type { RunApi } from './api'
import RunListPage from './RunListPage'

function runFixture(index: number): RunSummary {
  return {
    id: `run-${String(index).padStart(3, '0')}`,
    workflow_id: `workflow-${String(index % 5).padStart(2, '0')}`,
    status: index % 3 === 0 ? 'SUCCESS' : 'RUNNING',
    created_at: `2026-01-01T00:${String(index % 60).padStart(2, '0')}:00Z`,
  }
}

function eventFixture(index: number): EventView {
  return {
    id: `event-${String(index).padStart(4, '0')}`,
    workflow_run_id: `run-${String(index % 250).padStart(3, '0')}`,
    task_run_id: `task-${String(index).padStart(4, '0')}`,
    attempt_id: `attempt-${String(index).padStart(4, '0')}`,
    event_type: index % 2 === 0 ? 'TURN_STARTED' : 'TURN_COMPLETED',
    payload: { sequence: index },
    created_at: `2026-01-01T00:00:${String(index % 60).padStart(2, '0')}Z`,
  }
}

function runApi(listPage: RunApi['listPage']): RunApi {
  return {
    list: vi.fn(),
    listPage,
    start: vi.fn(),
    get: vi.fn(),
    tasks: vi.fn(),
    attempts: vi.fn(),
  }
}

describe('large history and event performance guard', () => {
  it('loads hundreds of runs with bounded fetches and no duplicate rendered rows', async () => {
    const user = userEvent.setup()
    const runs = Array.from({ length: 250 }, (_, index) => runFixture(index))
    const pages: RunSummary[][] = [runs.slice(0, 25)]
    for (let offset = 24; offset < runs.length; offset += 24) {
      pages.push([runs[offset - 1]!, ...runs.slice(offset, offset + 24)])
    }
    let pageIndex = 0
    const listPage = vi.fn(async () => {
      const items = pages[pageIndex++]!
      return { items, next_cursor: pageIndex < pages.length ? `cursor-${pageIndex}` : null }
    })

    render(<MemoryRouter><RunListPage api={runApi(listPage)} /></MemoryRouter>)
    expect(await screen.findByText('run-000')).toBeInTheDocument()

    while (screen.queryByRole('button', { name: 'Load more' })) {
      await user.click(screen.getByRole('button', { name: 'Load more' }))
    }

    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(250)
    expect(within(items[0]!).getByText('run-000')).toBeInTheDocument()
    expect(within(items[249]!).getByText('run-249')).toBeInTheDocument()
    expect(new Set(items.map((item) => item.textContent)).size).toBe(250)
    expect(listPage).toHaveBeenCalledTimes(pages.length)
  })

  it('filters thousands of events in stable order without duplicate rendered entries', async () => {
    const user = userEvent.setup()
    render(<EventLog events={Array.from({ length: 2000 }, (_, index) => eventFixture(index))} />)

    expect(screen.getAllByRole('listitem')).toHaveLength(2000)
    await user.selectOptions(screen.getByLabelText('Event type'), 'TURN_COMPLETED')

    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(1000)
    expect(within(items[0]!).getByText('Task: task-0001')).toBeInTheDocument()
    expect(within(items[999]!).getByText('Task: task-1999')).toBeInTheDocument()
    expect(new Set(items.map((item) => item.textContent)).size).toBe(1000)
  }, 30000)
})
