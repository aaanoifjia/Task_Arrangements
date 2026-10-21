import { describe, expect, it, vi } from 'vitest'

import { isTauriEnvironment, loadRuntimeState } from './runtime'

describe('desktop runtime bridge', () => {
  it('keeps browser mode on the relative API/WebSocket defaults', async () => {
    const invoker = vi.fn()

    expect(isTauriEnvironment({})).toBe(false)
    await expect(loadRuntimeState({}, invoker)).resolves.toBeNull()
    expect(invoker).not.toHaveBeenCalled()
  })

  it.each([
    { __TAURI_INTERNALS__: {} },
    { __TAURI__: {} },
  ])('detects a Tauri environment', (scope) => {
    expect(isTauriEnvironment(scope)).toBe(true)
  })

  it('invokes the runtime-state command in Tauri mode', async () => {
    const runtimeState = {
      baseUrl: 'http://127.0.0.1:43127',
      token: 'opaque-session-token',
    }
    const invoker = vi.fn().mockResolvedValue(runtimeState)

    await expect(loadRuntimeState({ __TAURI_INTERNALS__: {} }, invoker)).resolves.toEqual(runtimeState)
    expect(invoker).toHaveBeenCalledWith('runtime_state')
  })
})
