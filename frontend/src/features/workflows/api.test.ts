import { describe, expect, it, vi } from 'vitest'
import { fixtureWorkflow, fixtureWorkflowDetail, fixtureWorkflowSummary } from '../../test/fixtures'
import type { ApiClient } from '../../api/client'
import { createWorkflowApi } from './api'

function fakeClient(): ApiClient {
  return {
    listWorkflows: vi.fn().mockResolvedValue([fixtureWorkflowSummary]),
    getWorkflow: vi.fn().mockResolvedValue(fixtureWorkflowDetail),
    saveWorkflow: vi.fn().mockResolvedValue(fixtureWorkflowDetail),
    updateWorkflow: vi.fn().mockResolvedValue(fixtureWorkflowDetail),
    listRuns: vi.fn(), getRun: vi.fn(), startRun: vi.fn(), listTasks: vi.fn(), listAttempts: vi.fn(),
  }
}

describe('workflow API resource', () => {
  it('maps list/get/create/update to the M6 client', async () => {
    const client = fakeClient()
    const api = createWorkflowApi(client)
    await expect(api.list()).resolves.toEqual([fixtureWorkflowSummary])
    await expect(api.get('workflow-1')).resolves.toEqual(fixtureWorkflowDetail)
    await expect(api.create(fixtureWorkflow)).resolves.toEqual(fixtureWorkflowDetail)
    await expect(api.update('workflow-1', fixtureWorkflow)).resolves.toEqual(fixtureWorkflowDetail)
    expect(client.listWorkflows).toHaveBeenCalledOnce()
    expect(client.getWorkflow).toHaveBeenCalledWith('workflow-1')
    expect(client.saveWorkflow).toHaveBeenCalledWith(fixtureWorkflow)
    expect(client.updateWorkflow).toHaveBeenCalledWith('workflow-1', fixtureWorkflow)
  })
})
