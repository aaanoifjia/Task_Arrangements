import { BrowserRouter, Route, Routes } from 'react-router-dom'
import AppShell from './AppShell'
import WorkflowListPage from '../features/workflows/WorkflowListPage'
import WorkflowEditorPage from '../features/editor/WorkflowEditorPage'
import RunListPage from '../features/runs/RunListPage'
import RunDetailPage from '../features/runs/RunDetailPage'
import AboutPage from '../features/system/AboutPage'

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
          <Route path="/about" element={<AboutPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  )
}

