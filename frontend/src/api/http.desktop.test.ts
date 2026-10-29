import { beforeEach, describe, expect, it, vi } from 'vitest'
import { requestJson } from './http'

const { invoke } = vi.hoisted(() => ({ invoke: vi.fn() }))

vi.mock('@tauri-apps/api/core', () => ({ invoke }))

function response(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('desktop API runtime injection', () => {
  beforeEach(() => {
    invoke.mockReset()
    invoke.mockResolvedValue({ baseUrl: 'http://127.0.0.1:43127', token: 'opaque-token' })
    vi.stubGlobal('__TAURI_INTERNALS__', {})
  })

  it('uses the Tauri runtime state for default API clients', async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response([]))

    await requestJson('/api/workflows', {}, fetcher)

    expect(invoke).toHaveBeenCalledWith('runtime_state')
    expect(fetcher).toHaveBeenCalledWith(
      'http://127.0.0.1:43127/api/workflows',
      expect.objectContaining({
        headers: { Accept: 'application/json', Authorization: 'Bearer opaque-token' },
      }),
    )
  })
})
