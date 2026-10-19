import { BrowserRouter, Route, Routes } from 'react-router-dom'
import AppShell from './AppShell'
import WorkflowListPage from '../features/workflows/WorkflowListPage'
import WorkflowEditorPage from '../features/editor/WorkflowEditorPage'

function RunsPage() {
  return <section aria-labelledby="runs-heading"><h1 id="runs-heading">Run history</h1><p>Completed and active runs.</p></section>
}

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
          <Route path="/runs" element={<RunsPage />} />
          <Route path="/runs/:runId" element={<RunDetailPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  )
}

