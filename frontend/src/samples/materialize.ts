import type { TaskDefinition, WorkflowDefinition } from '../api/types'

const COPY_SUFFIX = '-copy'

const nextWorkflowId = (sampleId: string, existingIds: ReadonlySet<string>): string => {
  const baseId = `${sampleId}${COPY_SUFFIX}`
  if (!existingIds.has(baseId)) return baseId

  let index = 2
  while (existingIds.has(`${baseId}-${index}`)) index += 1
  return `${baseId}-${index}`
}

const cloneTask = (sampleTask: TaskDefinition, cwd: string): TaskDefinition => ({
  ...sampleTask,
  cwd,
  dependencies: [...sampleTask.dependencies],
  retry_policy: { ...sampleTask.retry_policy },
})

export const materializeSample = (
  sample: WorkflowDefinition,
  existingWorkflowIds: ReadonlySet<string>,
  cwd = '.',
): WorkflowDefinition => {
  const normalizedCwd = cwd.trim() || '.'
  return {
    ...sample,
    id: nextWorkflowId(sample.id, existingWorkflowIds),
    name: `${sample.name} (copy)`,
    description: sample.description,
    tasks: sample.tasks.map((sampleTask) => cloneTask(sampleTask, normalizedCwd)),
    edges: sample.edges.map((edge) => ({ ...edge })),
  }
}
