import { useEffect } from 'react'

export type UnsavedIndicatorProps = { dirty: boolean }

function UnsavedIndicator({ dirty }: UnsavedIndicatorProps) {
  useEffect(() => {
    if (!dirty) return undefined
    const warnBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault()
      event.returnValue = ''
    }
    window.addEventListener('beforeunload', warnBeforeUnload)
    return () => window.removeEventListener('beforeunload', warnBeforeUnload)
  }, [dirty])

  return <span role="status" data-testid="unsaved-indicator">{dirty ? 'Unsaved changes' : 'Saved'}</span>
}

export default UnsavedIndicator
