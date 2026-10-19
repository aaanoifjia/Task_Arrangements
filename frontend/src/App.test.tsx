import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('App', () => {
  it('mounts without a backend dependency', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: 'Codex Flow' })).toBeInTheDocument()
  })
})
