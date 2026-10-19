import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import WorkflowMetadataPanel from './WorkflowMetadataPanel'

describe('WorkflowMetadataPanel', () => {
  it('keeps the workflow ID stable and tracks metadata changes as dirty', () => {
    const onChange = vi.fn()
    render(<WorkflowMetadataPanel workflowId="workflow-1" name="Original" description="Details" onChange={onChange} />)

    const id = screen.getByLabelText('Workflow ID')
    expect(id).toHaveValue('workflow-1')
    expect(id).toHaveAttribute('readonly')
    expect(screen.getByTestId('metadata-dirty')).toHaveTextContent('Saved')
    fireEvent.change(screen.getByLabelText('Workflow name'), { target: { value: 'Updated' } })
    expect(onChange).toHaveBeenLastCalledWith({ name: 'Updated' })
    expect(screen.getByTestId('metadata-dirty')).toHaveTextContent('Unsaved changes')
    fireEvent.change(screen.getByLabelText('Workflow description'), { target: { value: '' } })
    expect(onChange).toHaveBeenLastCalledWith({ description: null })
  })

  it('supports an optional description', () => {
    render(<WorkflowMetadataPanel workflowId="workflow-2" name="Name" description={null} />)
    expect(screen.getByLabelText('Workflow description')).toHaveValue('')
  })
})
