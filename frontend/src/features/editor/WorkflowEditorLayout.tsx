import { useState } from 'react'
import type { EditorGraph } from './graphModel'
import TaskInspector from './TaskInspector'
import type { TaskBasicsChanges } from './fields/TaskBasicsFields'
import WorkflowCanvas from './WorkflowCanvas'
import ValidationPanel from './ValidationPanel'
import type { ValidationIssue } from './validation'
import WorkflowMetadataPanel, { type WorkflowMetadataChanges } from './WorkflowMetadataPanel'
import SaveWorkflowButton, { type SaveWorkflowButtonProps } from './SaveWorkflowButton'
import UnsavedIndicator from './UnsavedIndicator'
import { useEditorShortcuts } from './useEditorShortcuts'
import EditorEmptyState from './EditorEmptyState'
import StartRunButton, { type StartRunButtonProps } from '../runs/StartRunButton'
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
  startRunConfig?: Omit<StartRunButtonProps, 'hasBlockingIssues'>
  dirty?: boolean
  onDeleteTask?: (taskId: string) => void
  onAddTask?: () => void
  onTaskChange?: (taskId: string, changes: TaskBasicsChanges) => void
  onGraphChange?: (graph: EditorGraph) => void
  onConnect?: (source: string, target: string) => void
  onDisconnect?: (edgeId: string) => void
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
  startRunConfig,
  dirty = false,
  onDeleteTask,
  onAddTask,
  onTaskChange,
  onGraphChange,
  onConnect,
  onDisconnect,
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
      <p><a href={`/runs?workflow_id=${encodeURIComponent(workflowId)}`}>View workflow runs</a></p>
      {onAddTask && <div role="toolbar" aria-label="Workflow editor actions"><button type="button" onClick={onAddTask}>Add task</button></div>}
      <div className="workflow-editor-layout">
        <section className="workflow-editor-layout__canvas" aria-label="Workflow editor canvas panel">
          {graph.nodes.length === 0
            ? <EditorEmptyState onAddTask={onAddTask} />
            : <WorkflowCanvas
              graph={graph}
              selectedTaskId={activeTaskId}
              onSelectTask={selectTask}
              onConnect={onConnect}
              onDisconnect={onDisconnect}
            />}
        </section>
        <TaskInspector
          task={activeTask}
          existingTaskIds={graph.nodes.map((node) => node.id)}
          graph={graph}
          onTaskChange={(changes) => { if (activeTaskId) onTaskChange?.(activeTaskId, changes) }}
          onGraphChange={onGraphChange}
          onDeleteTask={() => { if (activeTaskId) deleteSelected(activeTaskId) }}
        />
      </div>
      <ValidationPanel issues={validationIssues} onSelectTask={selectTask} onSave={onSave} />
      {saveConfig && <SaveWorkflowButton {...saveConfig} hasBlockingIssues={validationIssues.length > 0} />}
      {startRunConfig && <StartRunButton {...startRunConfig} hasBlockingIssues={validationIssues.length > 0} />}
    </div>
  )
}

export default WorkflowEditorLayout
