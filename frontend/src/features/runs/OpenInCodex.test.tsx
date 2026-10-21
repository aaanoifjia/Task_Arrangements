import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import OpenInCodex, { buildCodexThreadUri, isValidCodexThreadUri, openCodexThread } from './OpenInCodex'

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

  it('validates the native URI and invokes the Tauri bridge only for codex schemes', async () => {
    const invoker = vi.fn().mockResolvedValue(undefined)
    expect(isValidCodexThreadUri('codex://threads/thread-1')).toBe(true)
    expect(isValidCodexThreadUri('https://example.test/thread-1')).toBe(false)
    await expect(openCodexThread('codex://threads/thread-1', { __TAURI_INTERNALS__: {} }, invoker)).resolves.toBe(true)
    expect(invoker).toHaveBeenCalledWith('codex://threads/thread-1')
    await expect(openCodexThread('https://example.test/thread-1', { __TAURI_INTERNALS__: {} }, invoker)).rejects.toThrow('invalid Codex thread URI')
  })
})
