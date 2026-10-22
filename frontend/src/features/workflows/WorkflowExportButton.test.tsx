import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { createApiClient, type WorkflowExportResponse } from '../../api/client'
import WorkflowExportButton from './WorkflowExportButton'

const payload: WorkflowExportResponse = {
  kind: 'codex_flow.workflow_definition',
  schema_version: 1,
  workflow: {
    id: 'workflow-1', name: 'Export me', description: null, tasks: [], edges: [],
  },
}

afterEach(() => { vi.restoreAllMocks() })

describe('WorkflowExportButton', () => {
  it('uses the export endpoint and downloads a sanitized deterministic filename', async () => {
    const user = userEvent.setup()
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }))
    const createObjectURL = vi.fn(() => 'blob:workflow')
    const revokeObjectURL = vi.fn()
    Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: createObjectURL })
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: revokeObjectURL })
    let downloadedFileName = ''
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
      downloadedFileName = this.download
    })

    render(
      <WorkflowExportButton
        workflowId="workflow/id"
        workflowName="My: Workflow / 1"
        exporter={(id) => createApiClient(fetcher).exportWorkflow(id)}
      />,
    )

    await user.click(screen.getByRole('button', { name: 'Export JSON' }))

    expect(fetcher).toHaveBeenCalledWith('/api/workflows/workflow%2Fid/export', expect.anything())
    expect(createObjectURL).toHaveBeenCalledWith(expect.any(Blob))
    expect(click).toHaveBeenCalled()
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:workflow')
    expect(downloadedFileName).toBe('My-Workflow-1.json')
  })

  it('does not mutate the workflow name while exporting', async () => {
    const user = userEvent.setup()
    const exporter = vi.fn().mockResolvedValue(payload)
    const originalName = 'A / workflow'
    vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:workflow')
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {})
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    render(<WorkflowExportButton workflowId="workflow-1" workflowName={originalName} exporter={exporter} />)
    await user.click(screen.getByRole('button', { name: 'Export JSON' }))

    expect(exporter).toHaveBeenCalledWith('workflow-1')
    expect(originalName).toBe('A / workflow')
  })
})
