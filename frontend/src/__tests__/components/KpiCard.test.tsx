/**
 * Testes para componente KpiCard
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Activity } from 'lucide-react'
import { KpiCard } from '@/components/dashboard/kpi-card'

describe('KpiCard', () => {
  const defaultProps = {
    title: 'Execuções Hoje',
    value: 42,
    icon: Activity,
  }

  it('renders title correctly', () => {
    render(<KpiCard {...defaultProps} />)
    expect(screen.getByText('Execuções Hoje')).toBeInTheDocument()
  })

  it('renders numeric value', () => {
    render(<KpiCard {...defaultProps} />)
    expect(screen.getByText('42')).toBeInTheDocument()
  })

  it('renders string value', () => {
    render(<KpiCard {...defaultProps} value="99%" />)
    expect(screen.getByText('99%')).toBeInTheDocument()
  })

  it('renders description when provided', () => {
    render(<KpiCard {...defaultProps} description="Últimas 24 horas" />)
    expect(screen.getByText(/Últimas 24 horas/)).toBeInTheDocument()
  })

  it('does not render description when not provided', () => {
    const { container } = render(<KpiCard {...defaultProps} />)
    expect(container.querySelector('.text-xs.text-muted-foreground.mt-1')).not.toBeInTheDocument()
  })

  it('renders up trend indicator', () => {
    render(<KpiCard {...defaultProps} description="Crescimento" trend="up" />)
    expect(screen.getByText('↑')).toBeInTheDocument()
    expect(screen.getByText('↑')).toHaveClass('text-green-500')
  })

  it('renders down trend indicator', () => {
    render(<KpiCard {...defaultProps} description="Queda" trend="down" />)
    expect(screen.getByText('↓')).toBeInTheDocument()
    expect(screen.getByText('↓')).toHaveClass('text-red-500')
  })

  it('does not render trend when neutral', () => {
    render(<KpiCard {...defaultProps} description="Estável" trend="neutral" />)
    expect(screen.queryByText('↑')).not.toBeInTheDocument()
    expect(screen.queryByText('↓')).not.toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(<KpiCard {...defaultProps} className="custom-class" />)
    expect(container.firstChild).toHaveClass('custom-class')
  })

  it('renders icon', () => {
    const { container } = render(<KpiCard {...defaultProps} />)
    const icon = container.querySelector('svg')
    expect(icon).toBeInTheDocument()
  })
})
