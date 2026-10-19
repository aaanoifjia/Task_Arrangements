import type { EditorGraph } from './graphModel'

export type ValidationIssueCode =
  | 'REQUIRED_FIELD'
  | 'DUPLICATE_TASK_ID'
  | 'NODE_TASK_ID_MISMATCH'
  | 'UNKNOWN_DEPENDENCY_TARGET'
  | 'UNKNOWN_EDGE_SOURCE'
  | 'UNKNOWN_EDGE_TARGET'
  | 'SELF_EDGE'
  | 'DUPLICATE_EDGE'
  | 'DEPENDENCY_EDGE_MISMATCH'
  | 'CYCLE'
  | 'CONTINUATION_SOURCE_REQUIRED'
  | 'UNKNOWN_CONTINUATION_SOURCE'
  | 'SELF_CONTINUATION_SOURCE'
  | 'NEW_THREAD_CONTINUATION_SOURCE'

export type ValidationIssue = {
  code: ValidationIssueCode
  message: string
  taskId?: string
}

export function validateEditorGraph(graph: EditorGraph): ValidationIssue[] {
  const issues: ValidationIssue[] = []
  const taskIds = graph.nodes.map((node) => node.data.task.id)
  const knownIds = new Set(taskIds)
  const duplicateIds = new Set(taskIds.filter((id, index) => taskIds.indexOf(id) !== index))
  for (const taskId of duplicateIds) issues.push({ code: 'DUPLICATE_TASK_ID', message: `Task ID is duplicated: ${taskId}`, taskId })

  for (const node of graph.nodes) {
    const task = node.data.task
    if (node.id !== task.id) issues.push({ code: 'NODE_TASK_ID_MISMATCH', message: `Node ID does not match task ID: ${node.id}`, taskId: task.id })
    for (const [field, value] of [['id', task.id], ['name', task.name], ['prompt', task.prompt], ['cwd', task.cwd]] as const) {
      if (!value.trim()) issues.push({ code: 'REQUIRED_FIELD', message: `${field} must not be blank.`, taskId: task.id })
    }
    const dependencySet = new Set<string>()
    for (const dependency of task.dependencies) {
      if (dependencySet.has(dependency)) issues.push({ code: 'DEPENDENCY_EDGE_MISMATCH', message: `Dependency is duplicated: ${dependency}`, taskId: task.id })
      dependencySet.add(dependency)
      if (!knownIds.has(dependency)) issues.push({ code: 'UNKNOWN_DEPENDENCY_TARGET', message: `Unknown dependency target: ${dependency}`, taskId: task.id })
    }
    if (task.execution_mode === 'CONTINUE_THREAD') {
      if (!task.continue_from_task_id) issues.push({ code: 'CONTINUATION_SOURCE_REQUIRED', message: 'CONTINUE_THREAD requires a source task.', taskId: task.id })
      else if (!knownIds.has(task.continue_from_task_id)) issues.push({ code: 'UNKNOWN_CONTINUATION_SOURCE', message: `Unknown continuation source: ${task.continue_from_task_id}`, taskId: task.id })
      else if (task.continue_from_task_id === task.id) issues.push({ code: 'SELF_CONTINUATION_SOURCE', message: 'A task cannot continue itself.', taskId: task.id })
    } else if (task.continue_from_task_id !== null) {
      issues.push({ code: 'NEW_THREAD_CONTINUATION_SOURCE', message: 'NEW_THREAD cannot have a continuation source.', taskId: task.id })
    }
  }

  const incoming = new Map<string, Set<string>>()
  const edgePairs = new Set<string>()
  for (const node of graph.nodes) incoming.set(node.data.task.id, new Set())
  for (const edge of graph.edges) {
    const pair = `${edge.source}->${edge.target}`
    if (edgePairs.has(pair)) issues.push({ code: 'DUPLICATE_EDGE', message: `Duplicate edge: ${pair}` })
    edgePairs.add(pair)
    if (!knownIds.has(edge.source)) issues.push({ code: 'UNKNOWN_EDGE_SOURCE', message: `Unknown edge source: ${edge.source}` })
    if (!knownIds.has(edge.target)) issues.push({ code: 'UNKNOWN_EDGE_TARGET', message: `Unknown edge target: ${edge.target}` })
    if (edge.source === edge.target) issues.push({ code: 'SELF_EDGE', message: `Self edge: ${pair}`, taskId: edge.source })
    if (knownIds.has(edge.source) && knownIds.has(edge.target)) incoming.get(edge.target)?.add(edge.source)
  }

  for (const node of graph.nodes) {
    const task = node.data.task
    const incomingDependencies = incoming.get(task.id) ?? new Set<string>()
    if (new Set(task.dependencies).size !== incomingDependencies.size || [...incomingDependencies].some((id) => !task.dependencies.includes(id))) {
      issues.push({ code: 'DEPENDENCY_EDGE_MISMATCH', message: `Dependencies and edges differ for task: ${task.id}`, taskId: task.id })
    }
  }

  const indegree = new Map<string, number>([...knownIds].map((id) => [id, 0]))
  const outgoing = new Map<string, string[]>([...knownIds].map((id) => [id, []]))
  for (const edge of graph.edges) {
    if (!knownIds.has(edge.source) || !knownIds.has(edge.target) || edge.source === edge.target) continue
    if (outgoing.get(edge.source)?.includes(edge.target)) continue
    outgoing.get(edge.source)?.push(edge.target)
    indegree.set(edge.target, (indegree.get(edge.target) ?? 0) + 1)
  }
  const available = [...knownIds].filter((id) => indegree.get(id) === 0).sort()
  let visited = 0
  while (available.length) {
    const current = available.shift()!
    visited += 1
    for (const target of outgoing.get(current) ?? []) {
      const nextDegree = (indegree.get(target) ?? 0) - 1
      indegree.set(target, nextDegree)
      if (nextDegree === 0) available.push(target)
    }
    available.sort()
  }
  if (visited !== knownIds.size) issues.push({ code: 'CYCLE', message: 'Dependency graph contains a cycle.' })
  return issues
}
