import { fireEvent, render } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { useEditorShortcuts } from './useEditorShortcuts'

function Harness(props: Parameters<typeof useEditorShortcuts>[0]) {
  useEditorShortcuts(props)
  return (
    <>
      <input aria-label="Editable field" />
      <div contentEditable aria-label="Editable region" />
    </>
  )
}

describe('useEditorShortcuts', () => {
  it('saves with Ctrl/Cmd+S and clears selection with Escape', () => {
    const onSave = vi.fn()
    const onClearSelection = vi.fn()
    render(<Harness selectedTaskId="A" onSave={onSave} onClearSelection={onClearSelection} />)
    fireEvent.keyDown(window, { key: 's', ctrlKey: true })
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(onSave).toHaveBeenCalledOnce()
    expect(onClearSelection).toHaveBeenCalledOnce()
  })

  it('deletes only when focus is not in an editable field', () => {
    const onDeleteSelected = vi.fn()
    const { getByLabelText } = render(<Harness selectedTaskId="A" onDeleteSelected={onDeleteSelected} />)
    fireEvent.keyDown(window, { key: 'Delete' })
    expect(onDeleteSelected).toHaveBeenCalledWith('A')
    onDeleteSelected.mockClear()
    fireEvent.keyDown(getByLabelText('Editable field'), { key: 'Backspace' })
    fireEvent.keyDown(getByLabelText('Editable region'), { key: 'Delete' })
    expect(onDeleteSelected).not.toHaveBeenCalled()
  })
})
