import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { fixtureWorkflow, fixtureWorkflowDetail } from '../../test/fixtures'
import SaveWorkflowButton from './SaveWorkflowButton'

describe('SaveWorkflowButton', () => {
  it('updates an existing workflow once and marks it saved', async () => {
    let resolveUpdate: ((value: typeof fixtureWorkflowDetail) => void) | undefined
    const update = vi.fn(() => new Promise<typeof fixtureWorkflowDetail>((resolve) => { resolveUpdate = resolve }))
    const onSaved = vi.fn()
    render(
      <SaveWorkflowButton
        workflowId="workflow-1"
        workflow={fixtureWorkflow}
        workflowApi={{ update }}
        dirty
        onSaved={onSaved}
      />,
    )

    const button = screen.getByRole('button', { name: 'Save workflow' })
    fireEvent.click(button)
    fireEvent.click(button)
    expect(update).toHaveBeenCalledTimes(1)
    expect(update).toHaveBeenCalledWith('workflow-1', fixtureWorkflow)
    expect(button).toBeDisabled()
    resolveUpdate?.(fixtureWorkflowDetail)
    await waitFor(() => expect(onSaved).toHaveBeenCalledOnce())
    expect(screen.getByRole('button', { name: 'Save workflow' })).not.toBeDisabled()
  })

  it('keeps the dirty save enabled and surfaces API errors', async () => {
    const update = vi.fn().mockRejectedValue(new Error('API unavailable'))
    const onSaved = vi.fn()
    render(<SaveWorkflowButton workflowId="workflow-1" workflow={fixtureWorkflow} workflowApi={{ update }} dirty onSaved={onSaved} />)
    fireEvent.click(screen.getByRole('button', { name: 'Save workflow' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('API unavailable')
    expect(onSaved).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'Save workflow' })).not.toBeDisabled()
  })

  it('disables Save while validation issues block the payload', () => {
    const update = vi.fn()
    render(<SaveWorkflowButton workflowId="workflow-1" workflow={fixtureWorkflow} workflowApi={{ update }} dirty hasBlockingIssues />)
    expect(screen.getByRole('button', { name: 'Save workflow' })).toBeDisabled()
    expect(update).not.toHaveBeenCalled()
  })
})
