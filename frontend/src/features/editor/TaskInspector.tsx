import type { TaskDefinition } from '../../api/types'
import TaskBasicsFields, { renameTaskInGraph, type TaskBasicsChanges } from './fields/TaskBasicsFields'
import PromptField from './fields/PromptField'
import ModelFields from './fields/ModelFields'
import ExecutionFields from './fields/ExecutionFields'
import RetryFields from './fields/RetryFields'
import ContinuationFields from './fields/ContinuationFields'
import type { EditorGraph } from './graphModel'
import './TaskInspector.css'

export type TaskInspectorProps = {
  task: TaskDefinition | null
  existingTaskIds?: string[]
  graph?: EditorGraph
  onTaskChange?: (changes: TaskBasicsChanges) => void
  onGraphChange?: (graph: EditorGraph) => void
  onDeleteTask?: () => void
}

function TaskInspector({ task, existingTaskIds, graph, onTaskChange, onGraphChange, onDeleteTask }: TaskInspectorProps) {
  if (!task) {
    return (
      <aside className="task-inspector task-inspector--empty" aria-label="Task inspector">
        <p>Select a task to inspect its configuration.</p>
      </aside>
    )
  }

  const handleTaskChange = (changes: TaskBasicsChanges) => {
    if (changes.id && graph && onGraphChange) {
      onGraphChange(renameTaskInGraph(graph, task.id, changes.id))
      return
    }
    onTaskChange?.(changes)
  }

  return (
    <aside className="task-inspector" aria-label="Task inspector">
      <h2>Task inspector</h2>
      {onDeleteTask && (
        <button
          className="task-inspector__delete"
          type="button"
          onClick={() => { if (window.confirm(`Delete task ${task.id}?`)) onDeleteTask() }}
        >
          Delete task
        </button>
      )}
      <dl>
        <div>
          <dt>Name</dt>
          <dd>{task.name}</dd>
        </div>
        <div>
          <dt>Task ID</dt>
          <dd>{task.id}</dd>
        </div>
      </dl>
      <TaskBasicsFields
        task={task}
        existingTaskIds={existingTaskIds ?? [task.id]}
        onChange={handleTaskChange}
      />
      <PromptField value={task.prompt} onChange={(prompt) => handleTaskChange({ prompt })} />
      <ModelFields
        model={task.model}
        reasoningEffort={task.reasoning_effort}
        onChange={handleTaskChange}
      />
      <ExecutionFields
        sandbox={task.sandbox}
        approvalMode={task.approval_mode}
        onChange={handleTaskChange}
      />
      <RetryFields
        timeoutSeconds={task.timeout_seconds}
        retryPolicy={task.retry_policy}
        onChange={handleTaskChange}
      />
      <ContinuationFields
        taskId={task.id}
        executionMode={task.execution_mode}
        continueFromTaskId={task.continue_from_task_id}
        availableTaskIds={existingTaskIds ?? [task.id]}
        onChange={handleTaskChange}
      />
    </aside>
  )
}

export default TaskInspector
