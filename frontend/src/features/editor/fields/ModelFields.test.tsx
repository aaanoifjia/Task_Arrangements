import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import ModelFields from './ModelFields'

describe('ModelFields', () => {
  it('serializes explicit values and empty values as null', () => {
    const onChange = vi.fn()
    const { rerender } = render(<ModelFields model={null} reasoningEffort={null} onChange={onChange} />)

    fireEvent.change(screen.getByLabelText('Model'), { target: { value: 'gpt-test' } })
    expect(onChange).toHaveBeenLastCalledWith({ model: 'gpt-test' })
    fireEvent.change(screen.getByLabelText('Reasoning effort'), { target: { value: 'high' } })
    expect(onChange).toHaveBeenLastCalledWith({ reasoning_effort: 'high' })
    rerender(<ModelFields model="gpt-test" reasoningEffort="high" onChange={onChange} />)
    fireEvent.change(screen.getByLabelText('Model'), { target: { value: '' } })
    expect(onChange).toHaveBeenLastCalledWith({ model: null })
  })

  it('renders existing values without inventing defaults', () => {
    render(<ModelFields model="custom-model" reasoningEffort="medium" onChange={() => undefined} />)
    expect(screen.getByLabelText('Model')).toHaveValue('custom-model')
    expect(screen.getByLabelText('Reasoning effort')).toHaveValue('medium')
  })
})
