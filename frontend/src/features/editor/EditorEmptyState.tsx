import './EditorEmptyState.css'

export type EditorEmptyStateProps = { onAddTask?: () => void }

function EditorEmptyState({ onAddTask }: EditorEmptyStateProps) {
  return (
    <section className="editor-empty-state" aria-label="Empty workflow editor">
      <h2>Start your workflow</h2>
      <p>Add a task, edit its Prompt and CWD, connect dependencies, Save, then Run.</p>
      <button type="button" onClick={onAddTask}>Add Task</button>
    </section>
  )
}

export default EditorEmptyState
