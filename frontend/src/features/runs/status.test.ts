import { render, screen } from '@testing-library/react'
import { createElement } from 'react'
import { ReactFlowProvider } from '@xyflow/react'
import { describe, expect, it } from 'vitest'
import { canonicalTaskStatuses, mapTaskStatus } from './status'
import RunTaskNode from './RunTaskNode'

describe('task status presentation', () => {
  it.each(canonicalTaskStatuses)('maps %s to a visible label and token', (status) => {
    const presentation = mapTaskStatus(status)
    expect(presentation.label).not.toBe('UNKNOWN')
    expect(presentation.token).not.toBe('unknown')
  })

  it('fails closed for unknown status values', () => {
    expect(mapTaskStatus('COMPLETED')).toEqual({ label: 'UNKNOWN', token: 'unknown' })
    expect(mapTaskStatus(null)).toEqual({ label: 'UNKNOWN', token: 'unknown' })
  })

  it('maps SKIPPED to the deterministic visible presentation', () => {
    expect(mapTaskStatus('SKIPPED')).toEqual({ label: 'Skipped', token: 'skipped' })
    expect(canonicalTaskStatuses).toContain('SKIPPED')
  })

  it('renders unknown status visibly on a run task node', () => {
    render(
      createElement(
        ReactFlowProvider,
        null,
        createElement(RunTaskNode, { data: { taskId: 'A', taskName: 'First task', status: 'unrecognized' } }),
      ),
    )
    expect(screen.getByRole('article', { name: 'Task First task' })).toHaveAttribute('data-status', 'unknown')
    expect(screen.getByRole('status')).toHaveTextContent('UNKNOWN')
  })
})
