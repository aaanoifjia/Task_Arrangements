import { describe, expect, it } from 'vitest'

import { STARTER_WORKFLOWS } from './workflows'
import { materializeSample } from './materialize'

describe('materializeSample', () => {
  it('creates a fresh valid copy with the default cwd', () => {
    const sample = STARTER_WORKFLOWS[0]
    const materialized = materializeSample(sample, new Set([sample.id]))

    expect(materialized.id).toBe('sample-linear-copy')
    expect(materialized.name).toBe('Linear starter (copy)')
    expect(materialized.tasks).toHaveLength(sample.tasks.length)
    expect(materialized.tasks.every((sampleTask) => sampleTask.cwd === '.')).toBe(true)
    expect(materialized.edges).toEqual(sample.edges)
    expect(materialized).not.toBe(sample)
  })

  it('uses the selected cwd and never mutates the source sample', () => {
    const sample = STARTER_WORKFLOWS[1]
    const originalCwds = sample.tasks.map((sampleTask) => sampleTask.cwd)
    const materialized = materializeSample(sample, new Set(), 'D:/selected/workspace')

    expect(materialized.tasks.every((sampleTask) => sampleTask.cwd === 'D:/selected/workspace')).toBe(true)
    expect(sample.tasks.map((sampleTask) => sampleTask.cwd)).toEqual(originalCwds)
    expect(materialized.tasks[0]).not.toBe(sample.tasks[0])
    expect(materialized.tasks[0].dependencies).not.toBe(sample.tasks[0].dependencies)
  })

  it('chooses the next deterministic ID instead of overwriting an existing workflow', () => {
    const sample = STARTER_WORKFLOWS[2]
    const existing = new Set(['sample-continuation', 'sample-continuation-copy', 'sample-continuation-copy-2'])
    const materialized = materializeSample(sample, existing, '')

    expect(materialized.id).toBe('sample-continuation-copy-3')
    expect(materialized.tasks.every((sampleTask) => sampleTask.cwd === '.')).toBe(true)
    expect(existing.has(materialized.id)).toBe(false)
    expect(materialized.tasks.find((sampleTask) => sampleTask.execution_mode === 'CONTINUE_THREAD'))
      .toMatchObject({ continue_from_task_id: 'context' })
  })
})
