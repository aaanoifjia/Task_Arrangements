/* eslint-disable react-refresh/only-export-components */
import { invoke } from '@tauri-apps/api/core'
import { isTauriEnvironment } from '../../desktop/runtime'

export function buildCodexThreadUri(threadId: string): string {
  return `codex://threads/${encodeURIComponent(threadId)}`
}

export function isValidCodexThreadUri(uri: string): boolean {
  return /^codex:\/\/threads\/[^/?#\\]+$/.test(uri)
}

export type NativeOpenInvoker = (uri: string) => Promise<unknown>

export async function openCodexThread(
  uri: string,
  scope: unknown = globalThis,
  invoker: NativeOpenInvoker = (value) => invoke('open_external', { uri: value }),
): Promise<boolean> {
  if (!isValidCodexThreadUri(uri)) throw new Error('invalid Codex thread URI')
  if (!isTauriEnvironment(scope)) return false
  await invoker(uri)
  return true
}

export type OpenInCodexProps = { threadId: string | null; nativeInvoker?: NativeOpenInvoker }

function OpenInCodex({ threadId, nativeInvoker }: OpenInCodexProps) {
  if (!threadId) return <span>Open in Codex unavailable</span>
  const uri = buildCodexThreadUri(threadId)
  if (isTauriEnvironment()) {
    return <button type="button" onClick={() => void openCodexThread(uri, globalThis, nativeInvoker)}>Open in Codex</button>
  }
  return <a href={uri}>Open in Codex</a>
}

export default OpenInCodex
