/**
 * Testes para componente SystemCard
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SystemCard } from '@/components/etl/system-card'
import type { Sistema } from '@/types/etl'

describe('SystemCard', () => {
  const mockSistema: Sistema = {
    id: 'maps',
    nome: 'MAPS',
    descricao: 'Upload e Processamento MAPS',
    icone: 'Map',
    ativo: true,
    ordem: 3,
    opcoes: { excel: true, pdf: false },
    status: 'IDLE',
    progresso: 0,
  }

  const mockOnToggle = vi.fn()
  const mockOnOptionToggle = vi.fn()

  const defaultProps = {
    sistema: mockSistema,
    onToggle: mockOnToggle,
    onOptionToggle: mockOnOptionToggle,
  }

  beforeEach(() => {
    mockOnToggle.mockClear()
    mockOnOptionToggle.mockClear()
  })

  it('renders sistema name', () => {
    render(<SystemCard {...defaultProps} />)
    expect(screen.getByText('MAPS')).toBeInTheDocument()
  })

  it('renders sistema description', () => {
    render(<SystemCard {...defaultProps} />)
    expect(screen.getByText('Upload e Processamento MAPS')).toBeInTheDocument()
  })

  it('renders switch in correct state', () => {
    render(<SystemCard {...defaultProps} />)
    const switchElement = screen.getByRole('switch')
    expect(switchElement).toBeChecked()
  })

  it('renders switch unchecked when sistema inactive', () => {
    const inactiveSistema = { ...mockSistema, ativo: false }
    render(<SystemCard {...defaultProps} sistema={inactiveSistema} />)
    const switchElement = screen.getByRole('switch')
    expect(switchElement).not.toBeChecked()
  })

  it('calls onToggle when switch is clicked', () => {
    render(<SystemCard {...defaultProps} />)
    const switchElement = screen.getByRole('switch')
    fireEvent.click(switchElement)
    expect(mockOnToggle).toHaveBeenCalledWith('maps', false)
  })

  it('renders options buttons', () => {
    render(<SystemCard {...defaultProps} />)
    // Procura pelos labels das opcoes
    expect(screen.getByText(/excel/i)).toBeInTheDocument()
    expect(screen.getByText(/pdf/i)).toBeInTheDocument()
  })

  it('calls onOptionToggle when option is clicked', () => {
    render(<SystemCard {...defaultProps} />)
    const excelButton = screen.getByRole('button', { name: /excel/i })
    fireEvent.click(excelButton)
    expect(mockOnOptionToggle).toHaveBeenCalledWith('maps', 'excel', false)
  })

  it('renders progress bar', () => {
    const sistemaWithProgress = { ...mockSistema, progresso: 50 }
    const { container } = render(<SystemCard {...defaultProps} sistema={sistemaWithProgress} />)
    const progressBar = container.querySelector('[style*="width: 50%"]')
    expect(progressBar).toBeInTheDocument()
  })

  it('renders default message when ativo', () => {
    render(<SystemCard {...defaultProps} />)
    expect(screen.getByText('Pronto para executar')).toBeInTheDocument()
  })

  it('renders "Desativado" message when inactive', () => {
    const inactiveSistema = { ...mockSistema, ativo: false }
    render(<SystemCard {...defaultProps} sistema={inactiveSistema} />)
    expect(screen.getByText('Desativado')).toBeInTheDocument()
  })

  it('renders custom message when provided', () => {
    const sistemaWithMessage = { ...mockSistema, mensagem: 'Processando arquivos...' }
    render(<SystemCard {...defaultProps} sistema={sistemaWithMessage} />)
    expect(screen.getByText('Processando arquivos...')).toBeInTheDocument()
  })

  it('applies running status styles', () => {
    const runningSistema = { ...mockSistema, status: 'RUNNING' as const }
    const { container } = render(<SystemCard {...defaultProps} sistema={runningSistema} />)
    expect(container.firstChild).toHaveClass('border-blue-500/50')
  })

  it('does not render option buttons when empty', () => {
    const sistemaNoOptions = { ...mockSistema, opcoes: {} }
    render(<SystemCard {...defaultProps} sistema={sistemaNoOptions} />)
    // Nao deve haver botoes de opcao (excel, pdf, etc)
    expect(screen.queryByRole('button', { name: /excel/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /pdf/i })).not.toBeInTheDocument()
  })
})
