import { BrowserRouter, Route, Routes } from 'react-router-dom'
import AppShell from './AppShell'
import WorkflowListPage from '../features/workflows/WorkflowListPage'
import WorkflowEditorPage from '../features/editor/WorkflowEditorPage'
import RunListPage from '../features/runs/RunListPage'

function RunDetailPage() {
  return <section aria-labelledby="run-heading"><h1 id="run-heading">Run detail</h1><p>Live run state and events.</p></section>
}

function NotFoundPage() {
  return <section aria-labelledby="not-found-heading"><h1 id="not-found-heading">Not found</h1><p>The requested view does not exist.</p></section>
}

export function AppRouter() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<WorkflowListPage />} />
          <Route path="/workflows/:workflowId" element={<WorkflowEditorPage />} />
          <Route path="/runs" element={<RunListPage />} />
          <Route path="/runs/:runId" element={<RunDetailPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  )
}

