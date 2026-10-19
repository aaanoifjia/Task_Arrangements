import { createApiClient, type ApiClient } from '../../api/client'
import type { WorkflowDefinition, WorkflowDetail, WorkflowSummary } from '../../api/types'

export type WorkflowApi = {
  list: () => Promise<WorkflowSummary[]>
  get: (workflowId: string) => Promise<WorkflowDetail>
  create: (workflow: WorkflowDefinition) => Promise<WorkflowDetail>
  update: (workflowId: string, workflow: WorkflowDefinition) => Promise<WorkflowDetail>
}

export function createWorkflowApi(client: ApiClient = createApiClient()): WorkflowApi {
  return {
    list: () => client.listWorkflows(),
    get: (workflowId) => client.getWorkflow(workflowId),
    create: (workflow) => client.saveWorkflow(workflow),
    update: (workflowId, workflow) => client.updateWorkflow(workflowId, workflow),
  }
}
