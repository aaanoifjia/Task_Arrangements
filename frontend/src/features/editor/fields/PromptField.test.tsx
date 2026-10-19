import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import PromptField from './PromptField'

describe('PromptField', () => {
  it('round-trips multiline prompt text without rewriting whitespace', () => {
    const onChange = vi.fn()
    const prompt = 'first line\n\n  indented line\nlast line'
    render(<PromptField value={prompt} onChange={onChange} />)

    const textarea = screen.getByLabelText('Task prompt')
    expect(textarea).toHaveValue(prompt)
    const edited = '  leading spaces\nsecond line\n\nfinal line  '
    fireEvent.change(textarea, { target: { value: edited } })
    expect(onChange).toHaveBeenCalledWith(edited)
  })

  it('accepts large prompt content as one exact value', () => {
    const onChange = vi.fn()
    const prompt = 'x'.repeat(20_000)
    render(<PromptField value="" onChange={onChange} />)
    fireEvent.change(screen.getByLabelText('Task prompt'), { target: { value: prompt } })
    expect(onChange).toHaveBeenCalledWith(prompt)
  })
})
