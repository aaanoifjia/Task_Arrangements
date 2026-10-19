import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import ValidationPanel from './ValidationPanel'

describe('ValidationPanel', () => {
  it('renders issues, selects referenced tasks, and disables Save', () => {
    const onSelectTask = vi.fn()
    const onSave = vi.fn()
    render(
      <ValidationPanel
        issues={[{ code: 'CYCLE', message: 'Dependency graph contains a cycle.', taskId: 'B' }]}
        onSelectTask={onSelectTask}
        onSave={onSave}
      />,
    )

    expect(screen.getByText('Dependency graph contains a cycle.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Select task B' }))
    expect(onSelectTask).toHaveBeenCalledWith('B')
    const saveButton = screen.getByRole('button', { name: 'Save workflow' })
    expect(saveButton).toBeDisabled()
    fireEvent.click(saveButton)
    expect(onSave).not.toHaveBeenCalled()
  })

  it('enables Save and reports a valid graph when no issues remain', () => {
    const onSave = vi.fn()
    const { rerender } = render(<ValidationPanel issues={[]} onSave={onSave} />)
    expect(screen.getByRole('status')).toHaveTextContent('Workflow is valid.')
    const saveButton = screen.getByRole('button', { name: 'Save workflow' })
    expect(saveButton).not.toBeDisabled()
    fireEvent.click(saveButton)
    expect(onSave).toHaveBeenCalledOnce()
    rerender(<ValidationPanel issues={[{ code: 'REQUIRED_FIELD', message: 'Name required.' }]} onSave={onSave} />)
    expect(screen.getByRole('button', { name: 'Save workflow' })).toBeDisabled()
  })
})
