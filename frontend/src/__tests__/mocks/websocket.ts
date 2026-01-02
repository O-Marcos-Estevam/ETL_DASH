/**
 * Mocks para o servico de WebSocket
 */
import { vi } from 'vitest'
import type { LogEntry, StatusUpdate } from '@/types/etl'

// Dados mock de log
export const mockLogEntry: LogEntry = {
  level: 'INFO',
  sistema: 'MAPS',
  mensagem: 'Iniciando processamento...',
  timestamp: '2024-01-01T10:00:00',
}

// Dados mock de status update
export const mockStatusUpdate: StatusUpdate = {
  status: 'RUNNING',
  progresso: 50,
  mensagem: 'Processando arquivos...',
}

// Mock do WebSocket Service
export const mockWebSocketService = {
  connect: vi.fn(),
  disconnect: vi.fn(),
  isConnected: vi.fn().mockReturnValue(true),
  onLog: vi.fn().mockReturnValue(() => {}),
  onStatusUpdate: vi.fn().mockReturnValue(() => {}),
  onConnectionChange: vi.fn().mockReturnValue(() => {}),
  onJobComplete: vi.fn().mockReturnValue(() => {}),
}

// Classe mock do WebSocket para testes mais detalhados
export class MockWebSocketClient {
  private logHandlers: ((log: LogEntry) => void)[] = []
  private statusHandlers: ((status: StatusUpdate) => void)[] = []
  private connectionHandlers: ((connected: boolean) => void)[] = []
  private jobCompleteHandlers: ((data: { job_id: number; status: string }) => void)[] = []

  connect = vi.fn()
  disconnect = vi.fn()
  isConnected = vi.fn().mockReturnValue(true)

  onLog(handler: (log: LogEntry) => void) {
    this.logHandlers.push(handler)
    return () => {
      this.logHandlers = this.logHandlers.filter((h) => h !== handler)
    }
  }

  onStatusUpdate(handler: (status: StatusUpdate) => void) {
    this.statusHandlers.push(handler)
    return () => {
      this.statusHandlers = this.statusHandlers.filter((h) => h !== handler)
    }
  }

  onConnectionChange(handler: (connected: boolean) => void) {
    this.connectionHandlers.push(handler)
    return () => {
      this.connectionHandlers = this.connectionHandlers.filter((h) => h !== handler)
    }
  }

  onJobComplete(handler: (data: { job_id: number; status: string }) => void) {
    this.jobCompleteHandlers.push(handler)
    return () => {
      this.jobCompleteHandlers = this.jobCompleteHandlers.filter((h) => h !== handler)
    }
  }

  // Metodos para simular eventos nos testes
  simulateLog(log: LogEntry) {
    this.logHandlers.forEach((h) => h(log))
  }

  simulateStatusUpdate(status: StatusUpdate) {
    this.statusHandlers.forEach((h) => h(status))
  }

  simulateConnectionChange(connected: boolean) {
    this.connectionHandlers.forEach((h) => h(connected))
  }

  simulateJobComplete(data: { job_id: number; status: string }) {
    this.jobCompleteHandlers.forEach((h) => h(data))
  }
}

// Helper para resetar mocks
export function resetWebSocketMocks() {
  mockWebSocketService.connect.mockClear()
  mockWebSocketService.disconnect.mockClear()
  mockWebSocketService.isConnected.mockClear()
  mockWebSocketService.onLog.mockClear()
  mockWebSocketService.onStatusUpdate.mockClear()
  mockWebSocketService.onConnectionChange.mockClear()
  mockWebSocketService.onJobComplete.mockClear()
}
