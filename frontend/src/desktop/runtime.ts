import { invoke } from '@tauri-apps/api/core'

export type DesktopRuntimeState = {
  baseUrl: string
  token: string
}

export type RuntimeInvoker = <T>(command: string) => Promise<T>

type RuntimeScope = {
  __TAURI_INTERNALS__?: unknown
  __TAURI__?: unknown
}

const defaultInvoker: RuntimeInvoker = <T>(command: string) => invoke<T>(command)

export function isTauriEnvironment(scope: unknown = globalThis): boolean {
  if (typeof scope !== 'object' || scope === null) return false
  const runtimeScope = scope as RuntimeScope
  return runtimeScope.__TAURI_INTERNALS__ !== undefined
    || runtimeScope.__TAURI__ !== undefined
}

export async function loadRuntimeState(
  scope: unknown = globalThis,
  invoker: RuntimeInvoker = defaultInvoker,
): Promise<DesktopRuntimeState | null> {
  if (!isTauriEnvironment(scope)) return null
  return invoker<DesktopRuntimeState>('runtime_state')
}
