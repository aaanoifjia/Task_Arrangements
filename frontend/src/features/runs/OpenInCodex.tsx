/* eslint-disable react-refresh/only-export-components */
export function buildCodexThreadUri(threadId: string): string {
  return `codex://threads/${encodeURIComponent(threadId)}`
}

export type OpenInCodexProps = { threadId: string | null }

function OpenInCodex({ threadId }: OpenInCodexProps) {
  if (!threadId) return <span>Open in Codex unavailable</span>
  return <a href={buildCodexThreadUri(threadId)}>Open in Codex</a>
}

export default OpenInCodex
