import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { fixtureRunDetail, fixtureRunSummary, fixtureTaskRun, fixtureWorkflowDetail, fixtureWorkflowSummary } from '../../test/fixtures'
import WorkflowEditorLayout from '../editor/WorkflowEditorLayout'
import type { WorkflowApi } from '../workflows/api'
import WorkflowListPage from '../workflows/WorkflowListPage'
import type { RunApi } from './api'
import RunDetailPage from './RunDetailPage'
import RunListPage from './RunListPage'

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

function workflowApi(): WorkflowApi {
  return { list: vi.fn().mockResolvedValue([fixtureWorkflowSummary]), get: vi.fn().mockResolvedValue(fixtureWorkflowDetail), create: vi.fn(), update: vi.fn() }
}

function runApi(): RunApi {
  return { start: vi.fn(), list: vi.fn().mockResolvedValue([fixtureRunSummary]), get: vi.fn().mockResolvedValue(fixtureRunDetail), tasks: vi.fn().mockResolvedValue([fixtureTaskRun]), attempts: vi.fn().mockResolvedValue([]) }
}

describe('workflow and run navigation', () => {
  it('links a workflow to its filtered run history and the editor links back to that filter', async () => {
    render(<MemoryRouter><WorkflowListPage api={workflowApi()} /></MemoryRouter>)
    expect(await screen.findByRole('link', { name: 'View runs' })).toHaveAttribute('href', '/runs?workflow_id=workflow-1')

    globalThis.ResizeObserver = ResizeObserverMock
    render(<MemoryRouter><WorkflowEditorLayout graph={{ nodes: [], edges: [] }} workflowId="workflow-1" /></MemoryRouter>)
    expect(screen.getByRole('link', { name: 'View workflow runs' })).toHaveAttribute('href', '/runs?workflow_id=workflow-1')
  })

  it('links run history rows back to workflows and run detail back to both workflow views', async () => {
    render(<MemoryRouter initialEntries={['/runs?workflow_id=workflow-1']}><RunListPage api={runApi()} /></MemoryRouter>)
    expect(await screen.findByRole('link', { name: 'Open workflow' })).toHaveAttribute('href', '/workflows/workflow-1')

    render(
      <MemoryRouter initialEntries={['/runs/run-1']}>
        <Routes><Route path="/runs/:runId" element={<RunDetailPage api={runApi()} />} /></Routes>
      </MemoryRouter>,
    )
    expect(await screen.findByRole('link', { name: 'Back to workflow' })).toHaveAttribute('href', '/workflows/workflow-1')
    expect(screen.getByRole('link', { name: 'Workflow runs' })).toHaveAttribute('href', '/runs?workflow_id=workflow-1')
  })
})
