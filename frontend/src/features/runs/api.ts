import { createApiClient, type ApiClient } from '../../api/client'
import type { AttemptView, RunDetail, RunStartResponse, RunSummary, TaskRunView } from '../../api/types'

export type RunApi = {
  start: (workflowId: string) => Promise<RunStartResponse>
  list: () => Promise<RunSummary[]>
  get: (runId: string) => Promise<RunDetail>
  tasks: (runId: string) => Promise<TaskRunView[]>
  attempts: (runId: string, taskId: string) => Promise<AttemptView[]>
}

export function createRunApi(client: ApiClient = createApiClient()): RunApi {
  return {
    start: (workflowId) => client.startRun(workflowId),
    list: () => client.listRuns(),
    get: (runId) => client.getRun(runId),
    tasks: (runId) => client.listTasks(runId),
    attempts: (runId, taskId) => client.listAttempts(runId, taskId),
  }
}
