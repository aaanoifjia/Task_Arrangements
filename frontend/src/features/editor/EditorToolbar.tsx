import type { Dispatch } from 'react'
import type { EditorAction } from './editorState'
import { createDefaultTask } from './editorState'
import type { EditorGraph } from './graphModel'
import './EditorToolbar.css'

export type EditorToolbarProps = {
  graph: EditorGraph
  dispatch: Dispatch<EditorAction>
}

function EditorToolbar({ graph, dispatch }: EditorToolbarProps) {
  const addTask = () => {
    const { task, position } = createDefaultTask(graph)
    dispatch({ type: 'add_task', task, position })
  }

  return (
    <div className="editor-toolbar" role="toolbar" aria-label="Workflow editor actions">
      <button type="button" onClick={addTask}>Add task</button>
    </div>
  )
}

export default EditorToolbar
