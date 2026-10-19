import { useEffect } from 'react'

export type EditorShortcutsProps = {
  selectedTaskId?: string | null
  onSave?: () => void
  onDeleteSelected?: (taskId: string) => void
  onClearSelection?: () => void
}

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  return target.matches('input, textarea, select, [contenteditable="true"]') || target.isContentEditable
}

export function useEditorShortcuts({ selectedTaskId, onSave, onDeleteSelected, onClearSelection }: EditorShortcutsProps) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
        event.preventDefault()
        onSave?.()
        return
      }
      if (event.key === 'Escape') {
        onClearSelection?.()
        return
      }
      if ((event.key === 'Delete' || event.key === 'Backspace') && !isEditableTarget(event.target) && selectedTaskId) {
        event.preventDefault()
        onDeleteSelected?.(selectedTaskId)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClearSelection, onDeleteSelected, onSave, selectedTaskId])
}
