import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import OpenInCodex, { buildCodexThreadUri } from './OpenInCodex'

describe('OpenInCodex', () => {
  it('builds an exact encoded Codex thread URI', () => {
    expect(buildCodexThreadUri('thread id/with?symbols')).toBe('codex://threads/thread%20id%2Fwith%3Fsymbols')
    render(<OpenInCodex threadId="thread id/with?symbols" />)
    expect(screen.getByRole('link', { name: 'Open in Codex' })).toHaveAttribute(
      'href', 'codex://threads/thread%20id%2Fwith%3Fsymbols',
    )
  })

  it('shows unavailable when the thread ID is missing', () => {
    render(<OpenInCodex threadId={null} />)
    expect(screen.getByText('Open in Codex unavailable')).toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })
})
