import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { STARTER_WORKFLOWS } from '../../samples/workflows'
import SampleWorkflowPicker from './SampleWorkflowPicker'

describe('SampleWorkflowPicker', () => {
  it('describes each canonical sample topology and purpose', () => {
    render(<SampleWorkflowPicker onSelect={vi.fn()} onCancel={vi.fn()} />)

    expect(screen.getByRole('dialog', { name: 'Try a sample workflow' })).toBeInTheDocument()
    expect(screen.getByText('Linear graph')).toBeInTheDocument()
    expect(screen.getByText('Fork/join graph')).toBeInTheDocument()
    expect(screen.getByText('Continuation chain')).toBeInTheDocument()
    expect(screen.getByText(STARTER_WORKFLOWS[0].description ?? '')).toBeInTheDocument()
  })

  it('supports keyboard selection and confirms the selected sample', async () => {
    const onSelect = vi.fn()
    const user = userEvent.setup()
    render(<SampleWorkflowPicker onSelect={onSelect} onCancel={vi.fn()} />)

    const options = screen.getAllByRole('radio')
    await user.click(options[1])
    expect(screen.getByRole('button', { name: 'Use selected sample' })).toBeEnabled()
    await user.keyboard('{Tab}{Enter}')
    expect(onSelect).toHaveBeenCalledWith(STARTER_WORKFLOWS[1])
  })

  it('cancels without selecting a sample', async () => {
    const onCancel = vi.fn()
    const user = userEvent.setup()
    render(<SampleWorkflowPicker onSelect={vi.fn()} onCancel={onCancel} />)

    await user.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(onCancel).toHaveBeenCalledOnce()
  })
})
