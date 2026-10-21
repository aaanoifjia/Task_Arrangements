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
      pauseRun: vi.fn().mockResolvedValue({ action: 'PAUSE' }),
      resumeRun: vi.fn().mockResolvedValue({ action: 'RESUME' }),
      retryTask: vi.fn().mockResolvedValue({ action: 'RETRY' }),
      cancelTask: vi.fn().mockResolvedValue({ action: 'CANCEL' }),
      skipTask: vi.fn().mockResolvedValue({ action: 'SKIP' }),
      markSuccessTask: vi.fn().mockResolvedValue({ action: 'MARK_SUCCESS' }),
    }
    const api = createRunApi(client as never)
    await expect(api.start('workflow-1')).resolves.toEqual({ run_id: 'run-1' })
    await expect(api.list()).resolves.toEqual([fixtureRunSummary])
    await expect(api.get('run-1')).resolves.toEqual(fixtureRunDetail)
    await expect(api.tasks('run-1')).resolves.toEqual([fixtureTaskRun])
    await expect(api.attempts('run-1', 'A')).resolves.toEqual([fixtureAttempt])
    await expect(api.pause('run-1')).resolves.toEqual({ action: 'PAUSE' })
    await expect(api.resume('run-1')).resolves.toEqual({ action: 'RESUME' })
    await expect(api.retry('run-1', 'A')).resolves.toEqual({ action: 'RETRY' })
    await expect(api.cancel('run-1', 'A')).resolves.toEqual({ action: 'CANCEL' })
    await expect(api.skip('run-1', 'A')).resolves.toEqual({ action: 'SKIP' })
    await expect(api.markSuccess('run-1', 'A')).resolves.toEqual({ action: 'MARK_SUCCESS' })
    expect(client.listAttempts).toHaveBeenCalledWith('run-1', 'A')
    expect(client.pauseRun).toHaveBeenCalledWith('run-1')
    expect(client.resumeRun).toHaveBeenCalledWith('run-1')
    expect(client.retryTask).toHaveBeenCalledWith('run-1', 'A')
    expect(client.cancelTask).toHaveBeenCalledWith('run-1', 'A')
    expect(client.skipTask).toHaveBeenCalledWith('run-1', 'A')
    expect(client.markSuccessTask).toHaveBeenCalledWith('run-1', 'A')
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
