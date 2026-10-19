import { describe, expect, it, vi } from 'vitest'
import { createApiClient } from '../../api/client'
import { ApiError } from '../../api/http'
import { fixtureAttempt, fixtureRunDetail, fixtureRunSummary, fixtureTaskRun } from '../../test/fixtures'
import { createRunApi } from './api'

describe('run API resource', () => {
  it('maps run and subresource operations to the public client', async () => {
    const client = {
      startRun: vi.fn().mockResolvedValue({ run_id: 'run-1' }),
      listRuns: vi.fn().mockResolvedValue([fixtureRunSummary]),
      getRun: vi.fn().mockResolvedValue(fixtureRunDetail),
      listTasks: vi.fn().mockResolvedValue([fixtureTaskRun]),
      listAttempts: vi.fn().mockResolvedValue([fixtureAttempt]),
    }
    const api = createRunApi(client as never)
    await expect(api.start('workflow-1')).resolves.toEqual({ run_id: 'run-1' })
    await expect(api.list()).resolves.toEqual([fixtureRunSummary])
    await expect(api.get('run-1')).resolves.toEqual(fixtureRunDetail)
    await expect(api.tasks('run-1')).resolves.toEqual([fixtureTaskRun])
    await expect(api.attempts('run-1', 'A')).resolves.toEqual([fixtureAttempt])
    expect(client.listAttempts).toHaveBeenCalledWith('run-1', 'A')
  })

  it('propagates ApiError from the public HTTP client', async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ error: { code: 'NOT_FOUND', message: 'missing run' } }), {
        status: 404, headers: { 'Content-Type': 'application/json' },
      }),
    )
    await expect(createRunApi(createApiClient(fetcher)).get('missing')).rejects.toEqual(
      new ApiError(404, 'NOT_FOUND', 'missing run'),
    )
  })
})
