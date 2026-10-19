import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { ApiError } from '../../api/http'
import type { RunApi } from './api'
import StartRunButton from './StartRunButton'

function api(start = vi.fn()): Pick<RunApi, 'start'> {
  return { start }
}

function LocationProbe() {
  const location = useLocation()
  return <output data-testid="location">{location.pathname}</output>
}

function renderButton(props: Partial<React.ComponentProps<typeof StartRunButton>> = {}) {
  return render(
    <MemoryRouter>
      <StartRunButton workflowId="workflow-1" runApi={api()} dirty={false} {...props} />
      <LocationProbe />
    </MemoryRouter>,
  )
}

describe('StartRunButton', () => {
  it('is disabled for dirty or invalid workflows', () => {
    const start = vi.fn()
    const { rerender } = render(
      <MemoryRouter><StartRunButton workflowId="workflow-1" runApi={api(start)} dirty /></MemoryRouter>,
    )
    expect(screen.getByRole('button', { name: 'Start run' })).toBeDisabled()
    rerender(
      <MemoryRouter><StartRunButton workflowId="workflow-1" runApi={api(start)} dirty={false} hasBlockingIssues /></MemoryRouter>,
    )
    expect(screen.getByRole('button', { name: 'Start run' })).toBeDisabled()
    expect(start).not.toHaveBeenCalled()
  })

  it('starts a saved valid run and navigates to its detail route', async () => {
    const start = vi.fn().mockResolvedValue({ run_id: 'run with spaces' })
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <StartRunButton workflowId="workflow-1" runApi={api(start)} dirty={false} />
        <LocationProbe />
      </MemoryRouter>,
    )
    await user.click(screen.getByRole('button', { name: 'Start run' }))
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('/runs/run%20with%20spaces'))
    expect(start).toHaveBeenCalledWith('workflow-1')
  })

  it('reports an active-run conflict without navigating', async () => {
    const start = vi.fn().mockRejectedValue(new ApiError(409, 'ACTIVE_RUN', 'workflow already running'))
    const user = userEvent.setup()
    renderButton({ runApi: api(start) })
    await user.click(screen.getByRole('button', { name: 'Start run' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('A run is already active for this workflow.')
    expect(screen.getByTestId('location')).toHaveTextContent('/')
  })
})
