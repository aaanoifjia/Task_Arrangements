import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { fixtureTaskRun } from '../../test/fixtures'
import RunSummaryPanel from './RunSummaryPanel'

describe('RunSummaryPanel', () => {
  it('shows mixed durable task counts and an explicit terminal result', () => {
    render(
      <RunSummaryPanel
        runStatus="SUCCESS"
        tasks={[
          fixtureTaskRun,
          { ...fixtureTaskRun, id: 'task-run-b', task_id: 'B', status: 'SUCCESS' },
          { ...fixtureTaskRun, id: 'task-run-c', task_id: 'C', status: 'FAILED' },
        ]}
      />,
    )
    expect(screen.getByTestId('run-result')).toHaveTextContent('Run result: SUCCESS')
    expect(screen.getByText('RUNNING')).toBeInTheDocument()
    expect(screen.getByText('FAILED')).toBeInTheDocument()
    expect(screen.getByText('SUCCESS')).toBeInTheDocument()
    expect(screen.getByTestId('status-count-SUCCESS')).toHaveTextContent('1')
    expect(screen.getByTestId('status-count-FAILED')).toHaveTextContent('1')
  })

  it('does not call a nonterminal run complete', () => {
    render(<RunSummaryPanel runStatus="RUNNING" tasks={[fixtureTaskRun]} />)
    expect(screen.getByTestId('run-result')).toHaveTextContent('Run is still in progress: RUNNING')
    expect(screen.getByTestId('run-result')).not.toHaveTextContent('Run result')
  })
})
