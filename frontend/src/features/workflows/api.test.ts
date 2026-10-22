import { describe, expect, it, vi } from 'vitest'
import { fixtureWorkflow, fixtureWorkflowDetail, fixtureWorkflowSummary } from '../../test/fixtures'
import { createApiClient, type ApiClient } from '../../api/client'
import { createWorkflowApi } from './api'

function fakeClient(): ApiClient {
  return {
    listWorkflows: vi.fn().mockResolvedValue([fixtureWorkflowSummary]),
    getWorkflow: vi.fn().mockResolvedValue(fixtureWorkflowDetail),
    exportWorkflow: vi.fn(),
    importWorkflow: vi.fn().mockResolvedValue(fixtureWorkflowDetail),
    getDiagnostics: vi.fn(),
    getSystemStatus: vi.fn(),
    downloadDiagnosticBundle: vi.fn(),
    downloadDatabaseBackup: vi.fn(),
    saveWorkflow: vi.fn().mockResolvedValue(fixtureWorkflowDetail),
    updateWorkflow: vi.fn().mockResolvedValue(fixtureWorkflowDetail),
    listRuns: vi.fn(), getRun: vi.fn(), startRun: vi.fn(), listTasks: vi.fn(), listAttempts: vi.fn(),
    listRunsPage: vi.fn(),
  }
}

describe('workflow API resource', () => {
  it('maps list/get/create/update/import to the M6 client', async () => {
    const client = fakeClient()
    const api = createWorkflowApi(client)
    await expect(api.list()).resolves.toEqual([fixtureWorkflowSummary])
    await expect(api.get('workflow-1')).resolves.toEqual(fixtureWorkflowDetail)
    await expect(api.create(fixtureWorkflow)).resolves.toEqual(fixtureWorkflowDetail)
    await expect(api.update('workflow-1', fixtureWorkflow)).resolves.toEqual(fixtureWorkflowDetail)
    if (!api.import) throw new Error('import mapping is unavailable')
    await expect(api.import({
      kind: 'codex_flow.workflow_definition', schema_version: 1, workflow: fixtureWorkflow,
    })).resolves.toEqual(fixtureWorkflowDetail)
    expect(client.listWorkflows).toHaveBeenCalledOnce()
    expect(client.getWorkflow).toHaveBeenCalledWith('workflow-1')
    expect(client.saveWorkflow).toHaveBeenCalledWith(fixtureWorkflow)
    expect(client.updateWorkflow).toHaveBeenCalledWith('workflow-1', fixtureWorkflow)
    expect(client.importWorkflow).toHaveBeenCalledWith({
      kind: 'codex_flow.workflow_definition', schema_version: 1, workflow: fixtureWorkflow,
    })
  })

  it('maps import endpoint and stable errors through the typed client', async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(new Response(
      JSON.stringify({ error: { code: 'WORKFLOW_IMPORT_CONFLICT', message: 'already exists' } }),
      { status: 409 },
    ))
    const client = createApiClient(fetcher)

    await expect(client.importWorkflow({
      kind: 'codex_flow.workflow_definition', schema_version: 1, workflow: fixtureWorkflow,
    })).rejects.toMatchObject({ status: 409, code: 'WORKFLOW_IMPORT_CONFLICT' })
    expect(fetcher).toHaveBeenCalledWith('/api/workflows/import', expect.objectContaining({ method: 'POST' }))
  })
})
