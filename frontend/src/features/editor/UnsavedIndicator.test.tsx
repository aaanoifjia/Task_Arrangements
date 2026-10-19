import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import UnsavedIndicator from './UnsavedIndicator'

describe('UnsavedIndicator', () => {
  it('shows saved and unsaved states', () => {
    const { rerender } = render(<UnsavedIndicator dirty={false} />)
    expect(screen.getByTestId('unsaved-indicator')).toHaveTextContent('Saved')
    rerender(<UnsavedIndicator dirty />)
    expect(screen.getByTestId('unsaved-indicator')).toHaveTextContent('Unsaved changes')
  })

  it('registers beforeunload only while dirty', () => {
    const { rerender } = render(<UnsavedIndicator dirty />)
    const dirtyEvent = new Event('beforeunload', { cancelable: true })
    window.dispatchEvent(dirtyEvent)
    expect(dirtyEvent.defaultPrevented).toBe(true)
    rerender(<UnsavedIndicator dirty={false} />)
    const cleanEvent = new Event('beforeunload', { cancelable: true })
    window.dispatchEvent(cleanEvent)
    expect(cleanEvent.defaultPrevented).toBe(false)
  })
})
