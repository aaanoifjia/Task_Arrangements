import { useEffect, useState } from 'react'
import type { TaskDefinition } from '../../../api/types'
import type { EditorGraph } from '../graphModel'

export type TaskBasicsChanges = Partial<Pick<TaskDefinition, 'id' | 'name' | 'cwd' | 'prompt' | 'model' | 'reasoning_effort'>>

export type TaskBasicsFieldsProps = {
  task: TaskDefinition
  existingTaskIds: string[]
  onChange: (changes: TaskBasicsChanges) => void
}

type DraftBasics = Pick<TaskDefinition, 'id' | 'name' | 'cwd'>

// eslint-disable-next-line react-refresh/only-export-components
export function renameTaskInGraph(graph: EditorGraph, taskId: string, nextId: string): EditorGraph {
  const normalizedId = nextId.trim()
  if (!normalizedId || graph.nodes.some((node) => node.id === normalizedId && node.id !== taskId)) return graph
  if (!graph.nodes.some((node) => node.id === taskId)) return graph

  const nextGraph = structuredClone(graph)
  for (const node of nextGraph.nodes) {
    if (node.id === taskId) {
      node.id = normalizedId
      node.data.task.id = normalizedId
    }
    node.data.task.dependencies = node.data.task.dependencies.map((dependency) => dependency === taskId ? normalizedId : dependency)
  }
  for (const edge of nextGraph.edges) {
    if (edge.source === taskId) edge.source = normalizedId
    if (edge.target === taskId) edge.target = normalizedId
    edge.id = `${edge.source}->${edge.target}`
  }
  return nextGraph
}

function TaskBasicsFields({ task, existingTaskIds, onChange }: TaskBasicsFieldsProps) {
  const [draft, setDraft] = useState<DraftBasics>({ id: task.id, name: task.name, cwd: task.cwd })
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setDraft({ id: task.id, name: task.name, cwd: task.cwd })
    setError(null)
  }, [task.id, task.name, task.cwd])

  const commit = (field: keyof DraftBasics, label: string) => {
    const value = draft[field].trim()
    if (!value) {
      setDraft((current) => ({ ...current, [field]: task[field] }))
      setError(`${label} is required.`)
      return
    }
    if (field === 'id' && value !== task.id && existingTaskIds.includes(value)) {
      setDraft((current) => ({ ...current, id: task.id }))
      setError('Task ID must be unique.')
      return
    }
    setError(null)
    if (value !== task[field]) onChange({ [field]: value })
    setDraft((current) => ({ ...current, [field]: value }))
  }

  return (
    <fieldset className="task-basics-fields">
      <legend>Task basics</legend>
      <label>
        Identifier
        <input
          aria-label="Task ID"
          value={draft.id}
          onChange={(event) => setDraft((current) => ({ ...current, id: event.target.value }))}
          onBlur={() => commit('id', 'Task ID')}
        />
      </label>
      <label>
        Name
        <input
          aria-label="Task name"
          value={draft.name}
          onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))}
          onBlur={() => commit('name', 'Task name')}
        />
      </label>
      <label>
        Working directory
        <input
          aria-label="Working directory"
          value={draft.cwd}
          onChange={(event) => setDraft((current) => ({ ...current, cwd: event.target.value }))}
          onBlur={() => commit('cwd', 'Working directory')}
        />
      </label>
      {error && <p role="alert">{error}</p>}
    </fieldset>
  )
}

export default TaskBasicsFields
