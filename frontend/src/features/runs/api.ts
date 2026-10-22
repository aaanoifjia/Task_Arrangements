import { createApiClient, type ControlApiClient } from '../../api/client'
import type {
  AttemptView, ManualActionResponse, RunDetail, RunHistoryPage, RunHistoryQuery,
  RunStartResponse, RunSummary, TaskRunView,
} from '../../api/types'

type RunApiCore = {
  start: (workflowId: string) => Promise<RunStartResponse>
  list: () => Promise<RunSummary[]>
  listPage?: (query?: RunHistoryQuery) => Promise<RunHistoryPage>
  get: (runId: string) => Promise<RunDetail>
  tasks: (runId: string) => Promise<TaskRunView[]>
  attempts: (runId: string, taskId: string) => Promise<AttemptView[]>
}

type RunControlMethods = {
  pause: (runId: string) => Promise<ManualActionResponse>
  resume: (runId: string) => Promise<ManualActionResponse>
  retry: (runId: string, taskId: string) => Promise<ManualActionResponse>
  cancel: (runId: string, taskId: string) => Promise<ManualActionResponse>
  skip: (runId: string, taskId: string) => Promise<ManualActionResponse>
  markSuccess: (runId: string, taskId: string) => Promise<ManualActionResponse>
}

export type RunApi = RunApiCore & Partial<RunControlMethods>
export type RunControlApi = RunApiCore & RunControlMethods

export function createRunApi(client: ControlApiClient = createApiClient()): RunControlApi {
  return {
    start: (workflowId) => client.startRun(workflowId),
    list: () => client.listRuns(),
    listPage: (query) => client.listRunsPage(query),
    get: (runId) => client.getRun(runId),
    tasks: (runId) => client.listTasks(runId),
    attempts: (runId, taskId) => client.listAttempts(runId, taskId),
    pause: (runId) => client.pauseRun(runId),
    resume: (runId) => client.resumeRun(runId),
    retry: (runId, taskId) => client.retryTask(runId, taskId),
    cancel: (runId, taskId) => client.cancelTask(runId, taskId),
    skip: (runId, taskId) => client.skipTask(runId, taskId),
    markSuccess: (runId, taskId) => client.markSuccessTask(runId, taskId),
  }
}
