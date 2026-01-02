/**
 * Mocks para o servico de API
 */
import { vi } from 'vitest'
import type { Sistema, ConfiguracaoETL } from '@/types/etl'

// Dados mock de sistemas
export const mockSistemas: Record<string, Sistema> = {
  amplis_reag: {
    id: 'amplis_reag',
    nome: 'AMPLIS (REAG)',
    descricao: 'Importacao de dados do AMPLIS (REAG)',
    icone: 'BarChart3',
    ativo: true,
    ordem: 1,
    opcoes: { csv: true, pdf: true },
    status: 'IDLE',
    progresso: 0,
  },
  maps: {
    id: 'maps',
    nome: 'MAPS',
    descricao: 'Upload e Processamento MAPS',
    icone: 'Map',
    ativo: true,
    ordem: 3,
    opcoes: { excel: true, pdf: true, ativo: true, passivo: true },
    status: 'IDLE',
    progresso: 0,
  },
  fidc: {
    id: 'fidc',
    nome: 'FIDC',
    descricao: 'Gestao de Direitos Creditorios',
    icone: 'FileSpreadsheet',
    ativo: false,
    ordem: 4,
    opcoes: {},
    status: 'IDLE',
    progresso: 0,
  },
  qore: {
    id: 'qore',
    nome: 'QORE',
    descricao: 'Processamento XML QORE',
    icone: 'FileCode',
    ativo: true,
    ordem: 7,
    opcoes: { excel: true, pdf: true, lote_pdf: false, lote_excel: false },
    status: 'IDLE',
    progresso: 0,
  },
}

// Dados mock de configuracao
export const mockConfig: ConfiguracaoETL = {
  versao: '2.0',
  ultimaModificacao: '2024-01-01T10:00:00',
  periodo: {
    dataInicial: '2024-01-01',
    dataFinal: '2024-01-31',
    usarD1Anbima: false,
  },
  sistemas: mockSistemas,
}

// Dados mock de credenciais
export const mockCredentials = {
  version: '2.0',
  amplis: {
    reag: { url: 'https://amplis.test', username: 'user_reag', password: '********' },
    master: { url: 'https://amplis.test', username: 'user_master', password: '********' },
  },
  maps: { url: 'https://maps.test', username: 'maps_user', password: '********' },
  paths: {
    csv: 'C:\\test\\csv',
    pdf: 'C:\\test\\pdf',
  },
}

// Mock das funcoes da API
export const mockApi = {
  getConfig: vi.fn().mockResolvedValue(mockConfig),
  saveConfig: vi.fn().mockResolvedValue({ success: true }),
  getSistemas: vi.fn().mockResolvedValue(mockSistemas),
  toggleSistema: vi.fn().mockResolvedValue({ success: true }),
  updateOpcao: vi.fn().mockResolvedValue({ success: true }),
  executePipeline: vi.fn().mockResolvedValue({ job_id: 1 }),
  getJobStatus: vi.fn().mockResolvedValue({ id: 1, status: 'completed' }),
  cancelExecution: vi.fn().mockResolvedValue({ success: true }),
  getCredentials: vi.fn().mockResolvedValue(mockCredentials),
  saveCredentials: vi.fn().mockResolvedValue({ success: true }),
  checkHealth: vi.fn().mockResolvedValue({ status: 'ok' }),
}

// Helper para resetar todos os mocks
export function resetApiMocks() {
  Object.values(mockApi).forEach((mock) => mock.mockClear())
}

// Helper para simular erro na API
export function mockApiError(method: keyof typeof mockApi, error: string) {
  mockApi[method].mockRejectedValueOnce(new Error(error))
}

// Helper para criar mock do fetch
export function createFetchMock(data: unknown, status = 200) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  })
}
