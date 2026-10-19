import { useState } from 'react'
import type { EditorGraph } from './graphModel'
import TaskInspector from './TaskInspector'
import WorkflowCanvas from './WorkflowCanvas'
import ValidationPanel from './ValidationPanel'
import type { ValidationIssue } from './validation'
import WorkflowMetadataPanel, { type WorkflowMetadataChanges } from './WorkflowMetadataPanel'
import SaveWorkflowButton, { type SaveWorkflowButtonProps } from './SaveWorkflowButton'
import UnsavedIndicator from './UnsavedIndicator'
import { useEditorShortcuts } from './useEditorShortcuts'
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
  saveConfig?: Omit<SaveWorkflowButtonProps, 'hasBlockingIssues'>
  dirty?: boolean
  onDeleteTask?: (taskId: string) => void
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
  saveConfig,
  dirty = false,
  onDeleteTask,
}: WorkflowEditorLayoutProps) {
  const [internalSelectedTaskId, setInternalSelectedTaskId] = useState<string | null>(null)
  const activeTaskId = selectedTaskId === undefined ? internalSelectedTaskId : selectedTaskId
  const activeTask = graph.nodes.find((node) => node.id === activeTaskId)?.data.task ?? null
  const selectTask = (taskId: string) => {
    setInternalSelectedTaskId(taskId)
    onSelectTask?.(taskId)
  }
  const clearSelection = () => {
    setInternalSelectedTaskId(null)
    onSelectTask?.(null)
  }
  const deleteSelected = (taskId: string) => {
    onDeleteTask?.(taskId)
    clearSelection()
  }
  useEditorShortcuts({ selectedTaskId: activeTaskId, onSave, onDeleteSelected: deleteSelected, onClearSelection: clearSelection })

  return (
    <div>
      <WorkflowMetadataPanel
        workflowId={workflowId}
        name={workflowName}
        description={workflowDescription}
        onChange={onMetadataChange}
      />
      <UnsavedIndicator dirty={dirty} />
      <div className="workflow-editor-layout">
        <section className="workflow-editor-layout__canvas" aria-label="Workflow editor canvas panel">
          <WorkflowCanvas graph={graph} selectedTaskId={activeTaskId} onSelectTask={selectTask} />
        </section>
        <TaskInspector task={activeTask} />
      </div>
      <ValidationPanel issues={validationIssues} onSelectTask={selectTask} onSave={onSave} />
      {saveConfig && <SaveWorkflowButton {...saveConfig} hasBlockingIssues={validationIssues.length > 0} />}
    </div>
  )
}

export default WorkflowEditorLayout
