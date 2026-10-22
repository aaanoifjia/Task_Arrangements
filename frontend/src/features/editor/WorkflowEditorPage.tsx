import { useEffect, useMemo, useReducer, useState } from 'react'
import { useParams } from 'react-router-dom'
import type { WorkflowDefinition } from '../../api/types'
import { createWorkflowApi, type WorkflowApi } from '../workflows/api'
import { createRunApi, type RunApi } from '../runs/api'
import { editorReducer, emptyEditorState, createDefaultTask } from './editorState'
import { graphToWorkflow, workflowToGraph } from './graphModel'
import { validateEditorGraph } from './validation'
import WorkflowEditorLayout from './WorkflowEditorLayout'
import WorkflowExportButton from '../workflows/WorkflowExportButton'

export type WorkflowEditorPageProps = { api?: WorkflowApi; runApi?: RunApi }

function isNotFound(cause: unknown): boolean {
  if (!cause || typeof cause !== 'object') return false
  const error = cause as { status?: number; code?: string }
  return error.status === 404 || error.code === 'NOT_FOUND'
}

function WorkflowEditorPage({ api, runApi }: WorkflowEditorPageProps) {
  const { workflowId } = useParams<{ workflowId: string }>()
  const stableApi = useMemo(() => api ?? createWorkflowApi(), [api])
  const stableRunApi = useMemo(() => runApi ?? createRunApi(), [runApi])
  const [editorState, dispatch] = useReducer(editorReducer, emptyEditorState)
  const [workflow, setWorkflow] = useState<WorkflowDefinition | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notFound, setNotFound] = useState(false)
  const [metadata, setMetadata] = useState({ name: '', description: null as string | null })

  useEffect(() => {
    let mounted = true
    if (!workflowId) return () => { mounted = false }
    setLoading(true)
    setError(null)
    setNotFound(false)
    void stableApi.get(workflowId).then((detail) => {
      if (!mounted) return
      setWorkflow(detail.workflow)
      setMetadata({ name: detail.workflow.name, description: detail.workflow.description })
      dispatch({ type: 'load', graph: workflowToGraph(detail.workflow) })
    }).catch((cause: unknown) => {
      if (!mounted) return
      setWorkflow(null)
      if (isNotFound(cause)) setNotFound(true)
      else setError(cause instanceof Error ? cause.message : 'Unable to load workflow.')
    }).finally(() => {
      if (mounted) setLoading(false)
    })
    return () => { mounted = false }
  }, [stableApi, workflowId])

  if (loading) return <p role="status">Loading workflow…</p>
  if (notFound) return <section aria-labelledby="workflow-not-found-heading"><h1 id="workflow-not-found-heading">Workflow not found</h1><p>The requested workflow does not exist.</p></section>
  if (error) return <section aria-labelledby="workflow-error-heading"><h1 id="workflow-error-heading">Unable to load workflow</h1><p role="alert">{error}</p></section>
  if (!workflow) return <p role="alert">Workflow data is unavailable.</p>

  const validationIssues = validateEditorGraph(editorState.graph)
  const workflowDraft = graphToWorkflow(editorState.graph, {
    id: workflow.id, name: metadata.name, description: metadata.description,
  })
  const addTask = () => {
    const { task, position } = createDefaultTask(editorState.graph)
    dispatch({ type: 'add_task', task, position })
  }

  return (
    <section aria-labelledby="workflow-editor-heading">
      <header>
        <h1 id="workflow-editor-heading">{workflow.name}</h1>
        <WorkflowExportButton workflowId={workflow.id} workflowName={workflow.name} />
      </header>
      <WorkflowEditorLayout
        graph={editorState.graph}
        workflowId={workflow.id}
        workflowName={metadata.name}
        workflowDescription={metadata.description}
        validationIssues={validationIssues}
        dirty={editorState.dirty}
        onAddTask={addTask}
        onDeleteTask={(taskId) => dispatch({ type: 'remove_task', taskId })}
        onTaskChange={(taskId, changes) => dispatch({ type: 'update_task', taskId, changes })}
        onGraphChange={(graph) => dispatch({ type: 'replace_graph', graph })}
        onConnect={(source, target) => dispatch({ type: 'connect', source, target })}
        onDisconnect={(edgeId) => dispatch({ type: 'disconnect', edgeId })}
        onMetadataChange={(changes) => {
          setMetadata((current) => ({ ...current, ...changes }))
          dispatch({ type: 'mark_dirty' })
        }}
        saveConfig={{
          workflowId: workflow.id,
          workflow: workflowDraft,
          workflowApi: stableApi,
          dirty: editorState.dirty,
          onSaved: () => dispatch({ type: 'mark_saved' }),
        }}
        startRunConfig={{ workflowId: workflow.id, runApi: stableRunApi, dirty: editorState.dirty }}
      />
    </section>
  )
}

export default WorkflowEditorPage
