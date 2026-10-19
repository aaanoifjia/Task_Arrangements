import type { ErrorResponse } from './types'

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

export async function requestJson<T>(
  input: string,
  init: RequestInit = {},
  fetcher: typeof fetch = fetch,
): Promise<T> {
  const response = await fetcher(input, {
    ...init,
    headers: { Accept: 'application/json', ...init.headers },
  })
  let body: unknown
  try {
    body = await response.json()
  } catch {
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
