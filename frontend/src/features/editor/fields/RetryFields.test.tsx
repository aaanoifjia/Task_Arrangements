import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import RetryFields from './RetryFields'

describe('RetryFields', () => {
  it('serializes positive timeout and retry values', () => {
    const onChange = vi.fn()
    const { rerender } = render(<RetryFields timeoutSeconds={null} retryPolicy={{ max_attempts: 1 }} onChange={onChange} />)

    fireEvent.change(screen.getByLabelText('Timeout seconds'), { target: { value: '30' } })
    expect(onChange).toHaveBeenLastCalledWith({ timeout_seconds: 30 })
    rerender(<RetryFields timeoutSeconds={30} retryPolicy={{ max_attempts: 1 }} onChange={onChange} />)
    fireEvent.change(screen.getByLabelText('Timeout seconds'), { target: { value: '' } })
    expect(onChange).toHaveBeenLastCalledWith({ timeout_seconds: null })
    fireEvent.change(screen.getByLabelText('Maximum attempts'), { target: { value: '3' } })
    expect(onChange).toHaveBeenLastCalledWith({ retry_policy: { max_attempts: 3 } })
  })

  it('rejects zero, negative, fractional, and non-numeric retry values', () => {
    const onChange = vi.fn()
    render(<RetryFields timeoutSeconds={null} retryPolicy={{ max_attempts: 1 }} onChange={onChange} />)

    fireEvent.change(screen.getByLabelText('Timeout seconds'), { target: { value: '0' } })
    expect(screen.getByRole('alert')).toHaveTextContent('Timeout must be a positive integer.')
    fireEvent.change(screen.getByLabelText('Maximum attempts'), { target: { value: '0' } })
    expect(screen.getByRole('alert')).toHaveTextContent('Maximum attempts must be at least 1.')
    expect(onChange).not.toHaveBeenCalled()
  })
})
