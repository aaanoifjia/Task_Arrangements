export type MockFetch = typeof fetch & { calls: Request[] }

export function createMockFetch(responses: Response[]): MockFetch {
  let index = 0
  const mock = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const request = new Request(input, init)
    mock.calls.push(request)
    const response = responses[index]
    index += 1
    if (!response) throw new Error('mock fetch response queue exhausted')
    return response.clone()
  }) as MockFetch
  mock.calls = []
  return mock
}

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}
