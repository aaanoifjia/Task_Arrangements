import { fireEvent, render, screen } from '@testing-library/react'
import { useReducer } from 'react'
import { describe, expect, it } from 'vitest'
import EditorToolbar from './EditorToolbar'
import { editorReducer, emptyEditorState } from './editorState'

function Harness() {
  const [state, dispatch] = useReducer(editorReducer, emptyEditorState)
  return (
    <>
      <EditorToolbar graph={state.graph} dispatch={dispatch} />
      <output data-testid="task-count">{state.graph.nodes.length}</output>
      <output data-testid="dirty-state">{String(state.dirty)}</output>
      <output data-testid="task-id">{state.graph.nodes[0]?.id ?? ''}</output>
    </>
  )
}

describe('EditorToolbar', () => {
  it('adds one deterministic task and marks the editor dirty', () => {
    render(<Harness />)
    fireEvent.click(screen.getByRole('button', { name: 'Add task' }))

    expect(screen.getByTestId('task-count')).toHaveTextContent('1')
    expect(screen.getByTestId('dirty-state')).toHaveTextContent('true')
    expect(screen.getByTestId('task-id')).toHaveTextContent('new-task-1')
  })
})
