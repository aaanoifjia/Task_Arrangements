import { useEffect, useMemo, useReducer, useState } from 'react'
import { useParams } from 'react-router-dom'
import type { WorkflowDefinition } from '../../api/types'
import { createWorkflowApi, type WorkflowApi } from '../workflows/api'
import { editorReducer, emptyEditorState } from './editorState'
import { workflowToGraph } from './graphModel'
import WorkflowEditorLayout from './WorkflowEditorLayout'

export type WorkflowEditorPageProps = { api?: WorkflowApi }

function isNotFound(cause: unknown): boolean {
  if (!cause || typeof cause !== 'object') return false
  const error = cause as { status?: number; code?: string }
  return error.status === 404 || error.code === 'NOT_FOUND'
}

function WorkflowEditorPage({ api }: WorkflowEditorPageProps) {
  const { workflowId } = useParams<{ workflowId: string }>()
  const stableApi = useMemo(() => api ?? createWorkflowApi(), [api])
  const [editorState, dispatch] = useReducer(editorReducer, emptyEditorState)
  const [workflow, setWorkflow] = useState<WorkflowDefinition | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    let mounted = true
    if (!workflowId) return () => { mounted = false }
    setLoading(true)
    setError(null)
    setNotFound(false)
    void stableApi.get(workflowId).then((detail) => {
      if (!mounted) return
      setWorkflow(detail.workflow)
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

  return (
    <section aria-labelledby="workflow-editor-heading">
      <h1 id="workflow-editor-heading">{workflow.name}</h1>
      <WorkflowEditorLayout
        graph={editorState.graph}
        workflowId={workflow.id}
        workflowName={workflow.name}
        workflowDescription={workflow.description}
        validationIssues={[]}
      />
    </section>
  )
}

export default WorkflowEditorPage
