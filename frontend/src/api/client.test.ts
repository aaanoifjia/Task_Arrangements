import { describe, expect, it, vi } from 'vitest'
import { createApiClient } from './client'

function response(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

describe('API client', () => {
  it('uses relative API paths and parses successful JSON', async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response(200, [{ id: 'w', name: 'Workflow' }]))
    await expect(createApiClient(fetcher).listWorkflows()).resolves.toEqual([{ id: 'w', name: 'Workflow' }])
    expect(fetcher).toHaveBeenCalledWith('/api/workflows', expect.objectContaining({ headers: { Accept: 'application/json' } }))
  })

  it.each([
    [404, 'NOT_FOUND'], [409, 'CONFLICT'], [500, 'SERVER_ERROR'],
  ])('maps stable %s errors', async (status, code) => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response(status, { error: { code, message: 'nope' } }))
    await expect(createApiClient(fetcher).listWorkflows()).rejects.toEqual(
      expect.objectContaining({ status, code, message: 'nope' }),
    )
  })

  it('rejects malformed successful responses without inferring state', async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(new Response('not-json', { status: 200 }))
    await expect(createApiClient(fetcher).listWorkflows()).rejects.toMatchObject({ code: 'INVALID_RESPONSE' })
  })

  it('maps all control actions with encoded run and task ids', async () => {
    const fetcher = vi.fn<typeof fetch>().mockImplementation(async () => response(200, { accepted: true }))
    const client = createApiClient(fetcher)
    const runId = 'run/1'
    const taskId = 'task 2'

    await client.pauseRun(runId)
    await client.resumeRun(runId)
    await client.retryTask(runId, taskId)
    await client.cancelTask(runId, taskId)
    await client.skipTask(runId, taskId)
    await client.markSuccessTask(runId, taskId)

    const expected = [
      '/api/runs/run%2F1/pause',
      '/api/runs/run%2F1/resume',
      '/api/runs/run%2F1/tasks/task%202/retry',
      '/api/runs/run%2F1/tasks/task%202/cancel',
      '/api/runs/run%2F1/tasks/task%202/skip',
      '/api/runs/run%2F1/tasks/task%202/mark-success',
    ]
    expect(fetcher).toHaveBeenCalledTimes(expected.length)
    expected.forEach((path, index) => {
      expect(fetcher).toHaveBeenNthCalledWith(
        index + 1,
        path,
        expect.objectContaining({ method: 'POST', headers: { Accept: 'application/json' } }),
      )
    })
  })
})
