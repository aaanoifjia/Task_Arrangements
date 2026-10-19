import type { Dispatch } from 'react'
import type { EditorAction } from './editorState'
import { createDefaultTask } from './editorState'
import type { EditorGraph } from './graphModel'
import './EditorToolbar.css'

export type EditorToolbarProps = {
  graph: EditorGraph
  dispatch: Dispatch<EditorAction>
  selectedTaskId?: string | null
  onDeleteTask?: (taskId: string) => void
}

function EditorToolbar({ graph, dispatch, selectedTaskId = null, onDeleteTask }: EditorToolbarProps) {
  const addTask = () => {
    const { task, position } = createDefaultTask(graph)
    dispatch({ type: 'add_task', task, position })
  }
  const deleteTask = () => {
    if (selectedTaskId && onDeleteTask && window.confirm(`Delete task ${selectedTaskId}?`)) onDeleteTask(selectedTaskId)
  }

  return (
    <div className="editor-toolbar" role="toolbar" aria-label="Workflow editor actions">
      <button type="button" onClick={addTask}>Add task</button>
      {onDeleteTask && (
        <button type="button" onClick={deleteTask} disabled={!selectedTaskId}>Delete task</button>
      )}
    </div>
  )
}

export default EditorToolbar
