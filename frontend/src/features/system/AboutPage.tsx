import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { createApiClient, type ApiClient, type SystemStatus } from '../../api/client'

type AboutApi = Pick<ApiClient, 'getSystemStatus'>
export type AboutPageProps = { api?: AboutApi }

function AboutPage({ api }: AboutPageProps) {
  const stableApi = useMemo(() => api ?? createApiClient(), [api])
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    void stableApi.getSystemStatus().then((result) => {
      if (mounted) setStatus(result)
    }).catch((cause: unknown) => {
      if (mounted) setError(cause instanceof Error ? cause.message : 'Unable to load runtime status.')
    }).finally(() => {
      if (mounted) setLoading(false)
    })
    return () => { mounted = false }
  }, [stableApi])

  return (
    <section aria-labelledby="about-heading">
      <h1 id="about-heading">About &amp; Runtime</h1>
      {loading && <p role="status">Loading runtime status…</p>}
      {error && <p role="alert">{error}</p>}
      {status && (
        <>
          <dl>
            <dt>Application version</dt><dd>{status.app_version}</dd>
            <dt>Backend version</dt><dd>{status.backend_version}</dd>
            <dt>Local backend</dt><dd>{status.runtime_available ? 'Available' : 'Unavailable'}</dd>
            <dt>Desktop mode</dt><dd>{status.desktop_mode ? 'Enabled' : 'Disabled'}</dd>
            <dt>Active runtime count</dt><dd>{status.active_runtime_count}</dd>
            <dt>Database schema</dt><dd>{status.schema_version}</dd>
          </dl>
          <Link to="/diagnostics">Open Diagnostics</Link>
        </>
      )}
    </section>
  )
}

export default AboutPage
