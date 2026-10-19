import type {
  AttemptView, RunDetail, RunStartResponse, RunSummary, TaskRunView,
  WorkflowDefinition, WorkflowDetail, WorkflowSummary,
} from './types'
import { requestJson } from './http'

const jsonHeaders = { 'Content-Type': 'application/json' }

export function createApiClient(fetcher: typeof fetch = fetch) {
  return {
    listWorkflows: () => requestJson<WorkflowSummary[]>('/api/workflows', {}, fetcher),
    getWorkflow: (id: string) => requestJson<WorkflowDetail>(`/api/workflows/${encodeURIComponent(id)}`, {}, fetcher),
    saveWorkflow: (workflow: WorkflowDefinition) => requestJson<WorkflowDetail>('/api/workflows', {
      method: 'POST', headers: jsonHeaders, body: JSON.stringify(workflow),
    }, fetcher),
    updateWorkflow: (id: string, workflow: WorkflowDefinition) => requestJson<WorkflowDetail>(
      `/api/workflows/${encodeURIComponent(id)}`,
      { method: 'PUT', headers: jsonHeaders, body: JSON.stringify(workflow) }, fetcher,
    ),
    listRuns: () => requestJson<RunSummary[]>('/api/runs', {}, fetcher),
    getRun: (id: string) => requestJson<RunDetail>(`/api/runs/${encodeURIComponent(id)}`, {}, fetcher),
    startRun: (workflowId: string) => requestJson<RunStartResponse>(
      `/api/workflows/${encodeURIComponent(workflowId)}/runs`, { method: 'POST' }, fetcher,
    ),
    listTasks: (runId: string) => requestJson<TaskRunView[]>(`/api/runs/${encodeURIComponent(runId)}/tasks`, {}, fetcher),
    listAttempts: (runId: string, taskId: string) => requestJson<AttemptView[]>(
      `/api/runs/${encodeURIComponent(runId)}/tasks/${encodeURIComponent(taskId)}/attempts`, {}, fetcher,
    ),
  }
}

export type ApiClient = ReturnType<typeof createApiClient>
