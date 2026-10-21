import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { fixtureRunSummary, fixtureTaskRun } from '../../test/fixtures'
import AttentionCenter from './AttentionCenter'

function renderCenter(api: { list: ReturnType<typeof vi.fn>; tasks: ReturnType<typeof vi.fn> }) {
  return render(<MemoryRouter><AttentionCenter api={api} /></MemoryRouter>)
}

describe('AttentionCenter', () => {
  it('counts and links NEEDS_ATTENTION tasks from loaded runs', async () => {
    const api = {
      list: vi.fn().mockResolvedValue([fixtureRunSummary, { ...fixtureRunSummary, id: 'run-2' }]),
      tasks: vi.fn().mockImplementation(async (runId: string) => runId === 'run-1'
        ? [{ ...fixtureTaskRun, status: 'NEEDS_ATTENTION' as const }]
        : [{ ...fixtureTaskRun, id: 'task-run-b', task_id: 'B', status: 'SUCCESS' as const }]),
    }
    renderCenter(api)
    expect(await screen.findByTestId('attention-count')).toHaveTextContent('1')
    const link = screen.getByRole('link', { name: /A.*Run run-1.*NEEDS_ATTENTION/ })
    expect(link).toHaveAttribute('href', '/runs/run-1?task_id=A')
    expect(api.tasks).toHaveBeenCalledWith('run-1')
    expect(api.tasks).toHaveBeenCalledWith('run-2')
  })

  it('shows an empty state when no task needs attention', async () => {
    const api = { list: vi.fn().mockResolvedValue([fixtureRunSummary]), tasks: vi.fn().mockResolvedValue([fixtureTaskRun]) }
    renderCenter(api)
    expect(await screen.findByText('No tasks need attention.')).toBeInTheDocument()
    expect(screen.getByTestId('attention-count')).toHaveTextContent('0')
  })

  it('shows a stable API error', async () => {
    const api = { list: vi.fn().mockRejectedValue(new Error('history unavailable')), tasks: vi.fn() }
    renderCenter(api)
    expect(await screen.findByRole('alert')).toHaveTextContent('history unavailable')
  })
})
