import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
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
    const runs = Array.from({ length: 250 }, (_, index) => runFixture(index))
    const pages: RunSummary[][] = [runs.slice(0, 25)]
    for (let offset = 25; offset < runs.length; offset += 24) {
      pages.push([runs[offset - 1]!, ...runs.slice(offset, offset + 24)])
    }
    let pageIndex = 0
    const listPage = vi.fn(async () => {
      const items = pages[pageIndex++]!
      return { items, next_cursor: pageIndex < pages.length ? `cursor-${pageIndex}` : null }
    })

    render(<MemoryRouter><RunListPage api={runApi(listPage)} /></MemoryRouter>)
    expect(await screen.findByText('run-000')).toBeInTheDocument()

    const runItems = () => screen.getByRole('list').querySelectorAll(':scope > li')
    for (let index = 1; index < pages.length; index += 1) {
      fireEvent.click(screen.getByRole('button', { name: 'Load more' }))
      const expectedCount = Math.min(25 + (index * 24), runs.length)
      await waitFor(() => expect(runItems()).toHaveLength(expectedCount))
    }

    const items = Array.from(runItems())
    expect(items).toHaveLength(runs.length)
    expect(within(items[0]! as HTMLElement).getByText('run-000')).toBeInTheDocument()
    expect(within(items[249]! as HTMLElement).getByText('run-249')).toBeInTheDocument()
    expect(new Set(items.map((item) => item.textContent)).size).toBe(250)
    expect(listPage).toHaveBeenCalledTimes(pages.length)
  }, 30000)

  it('filters thousands of events in stable order without duplicate rendered entries', async () => {
    render(<EventLog events={Array.from({ length: 2000 }, (_, index) => eventFixture(index))} />)

    const eventItems = () => screen.getByRole('list').querySelectorAll(':scope > li')
    expect(eventItems()).toHaveLength(2000)
    fireEvent.change(screen.getByLabelText('Event type'), { target: { value: 'TURN_COMPLETED' } })

    await waitFor(() => expect(eventItems()).toHaveLength(1000))
    const items = Array.from(eventItems())
    expect(items).toHaveLength(1000)
    expect(within(items[0]! as HTMLElement).getByText('Task: task-0001')).toBeInTheDocument()
    expect(within(items[999]! as HTMLElement).getByText('Task: task-1999')).toBeInTheDocument()
    expect(new Set(items.map((item) => item.textContent)).size).toBe(1000)
  }, 60000)
})
