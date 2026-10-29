import type { ErrorResponse } from './types'
import { isTauriEnvironment, loadRuntimeState } from '../desktop/runtime'

export type HttpRuntime = {
  baseUrl?: string
  token?: string
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

function isErrorResponse(value: unknown): value is ErrorResponse {
  if (typeof value !== 'object' || value === null || !('error' in value)) return false
  const error = (value as { error?: unknown }).error
  return typeof error === 'object' && error !== null
    && typeof (error as { code?: unknown }).code === 'string'
    && typeof (error as { message?: unknown }).message === 'string'
}

let desktopRuntimePromise: ReturnType<typeof loadRuntimeState> | undefined

async function resolveRuntime(runtime: HttpRuntime): Promise<HttpRuntime> {
  if (runtime.baseUrl || runtime.token || !isTauriEnvironment()) return runtime
  desktopRuntimePromise ??= loadRuntimeState().catch(() => null)
  const desktopRuntime = await desktopRuntimePromise
  return desktopRuntime ? { ...runtime, ...desktopRuntime } : runtime
}

export async function requestJson<T>(
  input: string,
  init: RequestInit = {},
  fetcher: typeof fetch = fetch,
  runtime: HttpRuntime = {},
): Promise<T> {
  const effectiveRuntime = await resolveRuntime(runtime)
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (init.headers && !(init.headers instanceof Headers)) Object.assign(headers, init.headers)
  if (effectiveRuntime.token) headers.Authorization = 'Bearer ' + effectiveRuntime.token
  const url = effectiveRuntime.baseUrl
    ? new URL(input, effectiveRuntime.baseUrl.replace(/\/+$/, '') + '/').toString()
    : input
  const response = await fetcher(url, {
    ...init,
    headers,
  })
  const rawBody = await response.text()
  let body: unknown
  try {
    body = rawBody ? JSON.parse(rawBody) : null
  } catch {
    if (!response.ok) {
      const preview = rawBody.trim().slice(0, 200)
      throw new ApiError(
        response.status,
        'HTTP_ERROR',
        `request failed with status ${response.status}${preview ? `: ${preview}` : ''}`,
      )
    }
    throw new ApiError(response.status, 'INVALID_RESPONSE', 'response was not valid JSON')
  }
  if (!response.ok) {
    if (isErrorResponse(body)) {
      throw new ApiError(response.status, body.error.code, body.error.message)
    }
    throw new ApiError(response.status, 'HTTP_ERROR', `request failed with status ${response.status}`)
  }
  return body as T
}
