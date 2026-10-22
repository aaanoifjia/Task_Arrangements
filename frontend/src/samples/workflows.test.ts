import { describe, expect, it } from 'vitest'

import { STARTER_WORKFLOWS } from './workflows'

describe('starter workflows', () => {
  it('provides linear, fork/join, and continuation examples', () => {
    expect(STARTER_WORKFLOWS.map((workflow) => workflow.id)).toEqual([
      'sample-linear',
      'sample-fork-join',
      'sample-continuation',
    ])
  })

  it('uses safe illustrative prompts and a machine-independent cwd', () => {
    for (const workflow of STARTER_WORKFLOWS) {
      for (const sampleTask of workflow.tasks) {
        expect(sampleTask.cwd).toBe('.')
        expect(sampleTask.prompt).toMatch(/^Illustrative placeholder:/)
        expect(sampleTask.prompt).not.toMatch(/(password|token|secret|api[_ -]?key)/i)
      }
    }
  })

  it('has valid references, dependency edges, and acyclic graphs', () => {
    for (const workflow of STARTER_WORKFLOWS) {
      const taskIds = new Set(workflow.tasks.map((sampleTask) => sampleTask.id))
      expect(taskIds.size).toBe(workflow.tasks.length)

      for (const edge of workflow.edges) {
        expect(taskIds.has(edge.source_task_id)).toBe(true)
        expect(taskIds.has(edge.target_task_id)).toBe(true)
        expect(edge.source_task_id).not.toBe(edge.target_task_id)
      }

      for (const sampleTask of workflow.tasks) {
        for (const dependency of sampleTask.dependencies) {
          expect(taskIds.has(dependency)).toBe(true)
          expect(workflow.edges).toContainEqual({
            source_task_id: dependency,
            target_task_id: sampleTask.id,
          })
        }
        if (sampleTask.execution_mode === 'CONTINUE_THREAD') {
          expect(sampleTask.continue_from_task_id).not.toBeNull()
          expect(taskIds.has(sampleTask.continue_from_task_id ?? '')).toBe(true)
        } else {
          expect(sampleTask.continue_from_task_id).toBeNull()
        }
      }

      const incoming = new Map([...taskIds].map((taskId) => [taskId, 0]))
      for (const edge of workflow.edges) incoming.set(edge.target_task_id, (incoming.get(edge.target_task_id) ?? 0) + 1)
      const queue = [...incoming].filter(([, count]) => count === 0).map(([taskId]) => taskId)
      let visited = 0
      while (queue.length > 0) {
        const current = queue.shift() as string
        visited += 1
        for (const edge of workflow.edges.filter(({ source_task_id }) => source_task_id === current)) {
          const remaining = (incoming.get(edge.target_task_id) ?? 0) - 1
          incoming.set(edge.target_task_id, remaining)
          if (remaining === 0) queue.push(edge.target_task_id)
        }
      }
      expect(visited).toBe(taskIds.size)
    }
  })
})
