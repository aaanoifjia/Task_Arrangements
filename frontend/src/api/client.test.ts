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
})
