import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import TaskStateNotice from './TaskStateNotice'

const expected: Record<string, string> = {
  FAILED: 'Task failed during execution.',
  INTERRUPTED: 'Task execution was interrupted',
  BLOCKED: 'Task is blocked because a dependency',
  NEEDS_ATTENTION: 'Task requires attention because execution',
}

describe('TaskStateNotice', () => {
  it.each(Object.entries(expected))('renders deterministic copy for %s without action controls', (status, copy) => {
    const { container } = render(<TaskStateNotice status={status} />)
    expect(screen.getByText(status)).toBeInTheDocument()
    expect(screen.getByText(new RegExp(copy))).toBeInTheDocument()
    expect(container.querySelector('button')).not.toBeInTheDocument()
  })

  it('does not speculate or add a notice for ordinary or unknown states', () => {
    const { container } = render(<><TaskStateNotice status="SUCCESS" /><TaskStateNotice status="UNKNOWN" /></>)
    expect(container).toBeEmptyDOMElement()
  })
})
