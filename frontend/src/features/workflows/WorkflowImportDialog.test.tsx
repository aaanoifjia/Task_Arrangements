import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { WorkflowDetail, WorkflowImportRequest } from '../../api/types'
import WorkflowImportDialog from './WorkflowImportDialog'

const imported: WorkflowDetail = {
  workflow: { id: 'imported', name: 'Imported', description: null, tasks: [], edges: [] },
}

const exportFile = (content: string) => new File([content], 'workflow.json', { type: 'application/json' })

describe('WorkflowImportDialog', () => {
  it('reads a JSON export, preserves explicit replacement policy, and reports the result', async () => {
    const user = userEvent.setup()
    const importer = vi.fn<(request: WorkflowImportRequest) => Promise<WorkflowDetail>>().mockResolvedValue(imported)
    const onImported = vi.fn()
    render(<WorkflowImportDialog importer={importer} onImported={onImported} onCancel={vi.fn()} />)

    await user.upload(screen.getByLabelText('Workflow JSON file'), exportFile(JSON.stringify({
      kind: 'codex_flow.workflow_definition', schema_version: 1, workflow: imported.workflow,
    })))
    await user.type(screen.getByLabelText('Replacement ID (optional)'), 'workflow-copy')
    await user.click(screen.getByRole('button', { name: 'Import workflow' }))

    expect(importer).toHaveBeenCalledWith(expect.objectContaining({ replacement_id: 'workflow-copy' }))
    expect(onImported).toHaveBeenCalledWith(imported)
  })

  it('shows malformed JSON without calling the importer', async () => {
    const user = userEvent.setup()
    const importer = vi.fn()
    render(<WorkflowImportDialog importer={importer} onImported={vi.fn()} onCancel={vi.fn()} />)

    await user.upload(screen.getByLabelText('Workflow JSON file'), exportFile('{invalid'))
    await user.click(screen.getByRole('button', { name: 'Import workflow' }))

    expect(screen.getByRole('alert')).toHaveTextContent(/JSON|Unexpected token/)
    expect(importer).not.toHaveBeenCalled()
  })

  it('supports keyboard-accessible cancellation', async () => {
    const user = userEvent.setup()
    const onCancel = vi.fn()
    render(<WorkflowImportDialog importer={vi.fn()} onImported={vi.fn()} onCancel={onCancel} />)

    await user.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(onCancel).toHaveBeenCalledOnce()
  })

  it('preserves Unicode and prompt whitespace across an import request', async () => {
    const user = userEvent.setup()
    const importer = vi.fn<(request: WorkflowImportRequest) => Promise<WorkflowDetail>>().mockResolvedValue(imported)
    const workflow = {
      ...imported.workflow,
      name: '流程 🚀',
      tasks: [{
        id: 'A', name: '节点 A', prompt: '  第一行  \n第二行\t  ', cwd: '.', dependencies: [],
        execution_mode: 'NEW_THREAD', continue_from_task_id: null, model: null, reasoning_effort: null,
        sandbox: 'workspace_write', approval_mode: null, timeout_seconds: null, retry_policy: { max_attempts: 1 },
      }],
    }
    render(<WorkflowImportDialog importer={importer} onImported={vi.fn()} onCancel={vi.fn()} />)

    await user.upload(screen.getByLabelText('Workflow JSON file'), exportFile(JSON.stringify({
      kind: 'codex_flow.workflow_definition', schema_version: 1, workflow,
    })))
    await user.click(screen.getByRole('button', { name: 'Import workflow' }))

    expect(importer).toHaveBeenCalledWith({
      kind: 'codex_flow.workflow_definition', schema_version: 1, workflow,
    })
  })
})
