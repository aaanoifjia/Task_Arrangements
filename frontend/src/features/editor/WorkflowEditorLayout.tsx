import { useState } from 'react'
import type { EditorGraph } from './graphModel'
import TaskInspector from './TaskInspector'
import WorkflowCanvas from './WorkflowCanvas'
import './WorkflowEditorLayout.css'

export type WorkflowEditorLayoutProps = {
  graph: EditorGraph
  selectedTaskId?: string | null
  onSelectTask?: (taskId: string | null) => void
}

function WorkflowEditorLayout({ graph, selectedTaskId, onSelectTask }: WorkflowEditorLayoutProps) {
  const [internalSelectedTaskId, setInternalSelectedTaskId] = useState<string | null>(null)
  const activeTaskId = selectedTaskId === undefined ? internalSelectedTaskId : selectedTaskId
  const activeTask = graph.nodes.find((node) => node.id === activeTaskId)?.data.task ?? null
  const selectTask = (taskId: string) => {
    setInternalSelectedTaskId(taskId)
    onSelectTask?.(taskId)
  }

  return (
    <div className="workflow-editor-layout">
      <section className="workflow-editor-layout__canvas" aria-label="Workflow editor canvas panel">
        <WorkflowCanvas graph={graph} selectedTaskId={activeTaskId} onSelectTask={selectTask} />
      </section>
      <TaskInspector task={activeTask} />
    </div>
  )
}

export default WorkflowEditorLayout
