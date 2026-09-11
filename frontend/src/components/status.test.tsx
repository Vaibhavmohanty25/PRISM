import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StatePanel } from './StatePanel'
import { StatusBadge } from './StatusBadge'

describe('shared product states', () => {
  it('renders backend categorical values as readable text', () => {
    render(<StatusBadge value="insufficient_data" />)
    expect(screen.getByText('Insufficient Data')).toBeInTheDocument()
  })

  it('renders an explicit unavailable state instead of a blank panel', () => {
    render(<StatePanel kind="unavailable" title="Forecast unavailable" message="No meaningful estimate was returned." />)
    expect(screen.getByRole('status')).toHaveTextContent('Forecast unavailable')
    expect(screen.getByText('No meaningful estimate was returned.')).toBeInTheDocument()
  })
})
