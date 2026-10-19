import type { TaskDefinition } from '../../api/types'
import TaskBasicsFields, { renameTaskInGraph, type TaskBasicsChanges } from './fields/TaskBasicsFields'
import PromptField from './fields/PromptField'
import ModelFields from './fields/ModelFields'
import type { EditorGraph } from './graphModel'
import './TaskInspector.css'

export type TaskInspectorProps = {
  task: TaskDefinition | null
  existingTaskIds?: string[]
  graph?: EditorGraph
  onTaskChange?: (changes: TaskBasicsChanges) => void
  onGraphChange?: (graph: EditorGraph) => void
}

function TaskInspector({ task, existingTaskIds, graph, onTaskChange, onGraphChange }: TaskInspectorProps) {
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
    </aside>
  )
}

export default TaskInspector
