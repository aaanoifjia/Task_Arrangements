import { useState } from 'react'
import type { EditorGraph } from './graphModel'
import TaskInspector from './TaskInspector'
import WorkflowCanvas from './WorkflowCanvas'
import ValidationPanel from './ValidationPanel'
import type { ValidationIssue } from './validation'
import WorkflowMetadataPanel, { type WorkflowMetadataChanges } from './WorkflowMetadataPanel'
import './WorkflowEditorLayout.css'

export type WorkflowEditorLayoutProps = {
  graph: EditorGraph
  selectedTaskId?: string | null
  onSelectTask?: (taskId: string | null) => void
  validationIssues?: ValidationIssue[]
  onSave?: () => void
  workflowId?: string
  workflowName?: string
  workflowDescription?: string | null
  onMetadataChange?: (changes: WorkflowMetadataChanges) => void
}

function WorkflowEditorLayout({
  graph,
  selectedTaskId,
  onSelectTask,
  validationIssues = [],
  onSave,
  workflowId = 'new-workflow',
  workflowName = 'Untitled workflow',
  workflowDescription = null,
  onMetadataChange,
}: WorkflowEditorLayoutProps) {
  const [internalSelectedTaskId, setInternalSelectedTaskId] = useState<string | null>(null)
  const activeTaskId = selectedTaskId === undefined ? internalSelectedTaskId : selectedTaskId
  const activeTask = graph.nodes.find((node) => node.id === activeTaskId)?.data.task ?? null
  const selectTask = (taskId: string) => {
    setInternalSelectedTaskId(taskId)
    onSelectTask?.(taskId)
  }

  return (
    <div>
      <WorkflowMetadataPanel
        workflowId={workflowId}
        name={workflowName}
        description={workflowDescription}
        onChange={onMetadataChange}
      />
      <div className="workflow-editor-layout">
        <section className="workflow-editor-layout__canvas" aria-label="Workflow editor canvas panel">
          <WorkflowCanvas graph={graph} selectedTaskId={activeTaskId} onSelectTask={selectTask} />
        </section>
        <TaskInspector task={activeTask} />
      </div>
      <ValidationPanel issues={validationIssues} onSelectTask={selectTask} onSave={onSave} />
    </div>
  )
}

export default WorkflowEditorLayout
