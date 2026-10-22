import type {
  AttemptView, RunDetail, RunStartResponse, RunSummary, TaskRunView,
  ManualActionResponse, WorkflowDefinition, WorkflowDetail, WorkflowSummary,
  WorkflowImportRequest, WorkflowExportResponse as WorkflowExportResponseType,
} from './types'
import { ApiError, requestJson as requestJsonWithRuntime, type HttpRuntime } from './http'

export type { WorkflowExportResponse } from './types'

export type DiagnosticSummary = {
  app_version: string
  backend_version: string
  os_name: string
  os_release: string
  python_version: string
  db_schema_version: number | null
  db_path_category: string
  active_run_count: number
  active_task_count: number
  recent_error_event_types: string[]
  log_directory_category: string
}

const jsonHeaders = { 'Content-Type': 'application/json' }

type ApiClientCore = {
  listWorkflows: () => Promise<WorkflowSummary[]>
  getWorkflow: (id: string) => Promise<WorkflowDetail>
  exportWorkflow: (id: string) => Promise<WorkflowExportResponseType>
  importWorkflow: (request: WorkflowImportRequest) => Promise<WorkflowDetail>
  getDiagnostics: () => Promise<DiagnosticSummary>
  downloadDiagnosticBundle: () => Promise<Blob>
  downloadDatabaseBackup: () => Promise<Blob>
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

export function createApiClient(fetcher: typeof fetch = fetch, runtime: HttpRuntime = {}): ControlApiClient {
  const requestJson = <T>(input: string, init: RequestInit = {}, legacyFetcher?: typeof fetch) => {
    void legacyFetcher
    return requestJsonWithRuntime<T>(input, init, fetcher, runtime)
  }
  return {
    listWorkflows: () => requestJson<WorkflowSummary[]>('/api/workflows', {}, fetcher),
    getWorkflow: (id: string) => requestJson<WorkflowDetail>(`/api/workflows/${encodeURIComponent(id)}`, {}, fetcher),
    exportWorkflow: (id: string) => requestJson<WorkflowExportResponseType>(
      `/api/workflows/${encodeURIComponent(id)}/export`, {}, fetcher,
    ),
    importWorkflow: (request: WorkflowImportRequest) => requestJson<WorkflowDetail>('/api/workflows/import', {
      method: 'POST', headers: jsonHeaders, body: JSON.stringify(request),
    }, fetcher),
    getDiagnostics: () => requestJson<DiagnosticSummary>('/api/system/diagnostics', {}, fetcher),
    downloadDiagnosticBundle: async () => {
      const headers: Record<string, string> = { Accept: 'application/zip' }
      if (runtime.token) headers.Authorization = 'Bearer ' + runtime.token
      const url = runtime.baseUrl
        ? new URL('/api/system/diagnostics/bundle', runtime.baseUrl.replace(/\/+$/, '') + '/').toString()
        : '/api/system/diagnostics/bundle'
      const response = await fetcher(url, { headers })
      if (!response.ok) throw new ApiError(response.status, 'HTTP_ERROR', `request failed with status ${response.status}`)
      return response.blob()
    },
    downloadDatabaseBackup: async () => {
      const headers: Record<string, string> = { Accept: 'application/octet-stream' }
      if (runtime.token) headers.Authorization = 'Bearer ' + runtime.token
      const url = runtime.baseUrl
        ? new URL('/api/system/database/backup', runtime.baseUrl.replace(/\/+$/, '') + '/').toString()
        : '/api/system/database/backup'
      const response = await fetcher(url, { headers })
      if (!response.ok) throw new ApiError(response.status, 'HTTP_ERROR', `request failed with status ${response.status}`)
      return response.blob()
    },
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
