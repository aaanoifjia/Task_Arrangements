import { useEffect, useMemo, useState } from 'react'
import { createApiClient, type ApiClient, type DiagnosticSummary } from '../../api/client'

type DiagnosticsApi = Pick<ApiClient, 'getDiagnostics' | 'downloadDiagnosticBundle' | 'downloadDatabaseBackup'>
type DiagnosticsPanelProps = { api?: DiagnosticsApi }

function DiagnosticsPanel({ api }: DiagnosticsPanelProps) {
  const stableApi = useMemo(() => api ?? createApiClient(), [api])
  const [summary, setSummary] = useState<DiagnosticSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const [backupDownloading, setBackupDownloading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    void stableApi.getDiagnostics().then((result) => {
      if (mounted) setSummary(result)
    }).catch((cause: unknown) => {
      if (mounted) setError(cause instanceof Error ? cause.message : 'Unable to load diagnostics')
    }).finally(() => {
      if (mounted) setLoading(false)
    })
    return () => { mounted = false }
  }, [stableApi])

  const downloadBundle = async () => {
    setDownloading(true)
    setError(null)
    try {
      const blob = await stableApi.downloadDiagnosticBundle()
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = 'codex-flow-diagnostics.zip'
      anchor.click()
      URL.revokeObjectURL(url)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to download diagnostics')
    } finally {
      setDownloading(false)
    }
  }

  const downloadDatabaseBackup = async () => {
    setBackupDownloading(true)
    setError(null)
    try {
      const blob = await stableApi.downloadDatabaseBackup()
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = 'codex-flow-backup.sqlite3'
      anchor.click()
      URL.revokeObjectURL(url)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to download database backup')
    } finally {
      setBackupDownloading(false)
    }
  }

  if (loading) return <p role="status">Loading diagnostics…</p>
  if (error && !summary) return <section aria-labelledby="diagnostics-heading"><h1 id="diagnostics-heading">Diagnostics</h1><p role="alert">{error}</p></section>
  if (!summary) return <p role="alert">Diagnostics are unavailable.</p>

  return (
    <section aria-labelledby="diagnostics-heading">
      <h1 id="diagnostics-heading">Diagnostics</h1>
      <p>Safe operational metadata for troubleshooting. Prompts, tokens, and raw paths are excluded.</p>
      <dl>
        <dt>Application version</dt><dd>{summary.app_version}</dd>
        <dt>Backend version</dt><dd>{summary.backend_version}</dd>
        <dt>Operating system</dt><dd>{summary.os_name} {summary.os_release}</dd>
        <dt>Python</dt><dd>{summary.python_version}</dd>
        <dt>Database schema</dt><dd>{summary.db_schema_version ?? 'Unavailable'}</dd>
        <dt>Database path</dt><dd>{summary.db_path_category}</dd>
        <dt>Log directory</dt><dd>{summary.log_directory_category}</dd>
        <dt>Active runs</dt><dd>{summary.active_run_count}</dd>
        <dt>Active tasks</dt><dd>{summary.active_task_count}</dd>
        <dt>Recent errors</dt><dd>{summary.recent_error_event_types.join(', ') || 'None'}</dd>
      </dl>
      {error && <p role="alert">{error}</p>}
      <button type="button" onClick={() => void downloadBundle()} disabled={downloading}>
        {downloading ? 'Preparing bundle…' : 'Download diagnostic bundle'}
      </button>
      <p>Database backups contain workflow and run data. Store the downloaded file securely.</p>
      <button type="button" onClick={() => void downloadDatabaseBackup()} disabled={backupDownloading}>
        {backupDownloading ? 'Preparing database backup…' : 'Download database backup'}
      </button>
    </section>
  )
}

export default DiagnosticsPanel
