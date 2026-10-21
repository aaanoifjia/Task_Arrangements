import type {
  AttemptView, RunDetail, RunStartResponse, RunSummary, TaskRunView,
  ManualActionResponse, WorkflowDefinition, WorkflowDetail, WorkflowSummary,
} from './types'
import { requestJson } from './http'

const jsonHeaders = { 'Content-Type': 'application/json' }

type ApiClientCore = {
  listWorkflows: () => Promise<WorkflowSummary[]>
  getWorkflow: (id: string) => Promise<WorkflowDetail>
  saveWorkflow: (workflow: WorkflowDefinition) => Promise<WorkflowDetail>
  updateWorkflow: (id: string, workflow: WorkflowDefinition) => Promise<WorkflowDetail>
  listRuns: () => Promise<RunSummary[]>
  getRun: (id: string) => Promise<RunDetail>
  startRun: (workflowId: string) => Promise<RunStartResponse>
  listTasks: (runId: string) => Promise<TaskRunView[]>
  listAttempts: (runId: string, taskId: string) => Promise<AttemptView[]>
}

export type ApiClient = ApiClientCore

export type ControlApiClient = ApiClientCore & {
  pauseRun: (runId: string) => Promise<ManualActionResponse>
  resumeRun: (runId: string) => Promise<ManualActionResponse>
  retryTask: (runId: string, taskId: string) => Promise<ManualActionResponse>
  cancelTask: (runId: string, taskId: string) => Promise<ManualActionResponse>
  skipTask: (runId: string, taskId: string) => Promise<ManualActionResponse>
  markSuccessTask: (runId: string, taskId: string) => Promise<ManualActionResponse>
}

export function createApiClient(fetcher: typeof fetch = fetch): ControlApiClient {
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
    pauseRun: (runId: string) => requestJson<ManualActionResponse>(
      `/api/runs/${encodeURIComponent(runId)}/pause`, { method: 'POST' }, fetcher,
    ),
    resumeRun: (runId: string) => requestJson<ManualActionResponse>(
      `/api/runs/${encodeURIComponent(runId)}/resume`, { method: 'POST' }, fetcher,
    ),
    retryTask: (runId: string, taskId: string) => requestJson<ManualActionResponse>(
      `/api/runs/${encodeURIComponent(runId)}/tasks/${encodeURIComponent(taskId)}/retry`,
      { method: 'POST' }, fetcher,
    ),
    cancelTask: (runId: string, taskId: string) => requestJson<ManualActionResponse>(
      `/api/runs/${encodeURIComponent(runId)}/tasks/${encodeURIComponent(taskId)}/cancel`,
      { method: 'POST' }, fetcher,
    ),
    skipTask: (runId: string, taskId: string) => requestJson<ManualActionResponse>(
      `/api/runs/${encodeURIComponent(runId)}/tasks/${encodeURIComponent(taskId)}/skip`,
      { method: 'POST' }, fetcher,
    ),
    markSuccessTask: (runId: string, taskId: string) => requestJson<ManualActionResponse>(
      `/api/runs/${encodeURIComponent(runId)}/tasks/${encodeURIComponent(taskId)}/mark-success`,
      { method: 'POST' }, fetcher,
    ),
  }
}
