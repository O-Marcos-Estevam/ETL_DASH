/**
 * Testes para servico de API
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  getConfig,
  saveConfig,
  getSistemas,
  toggleSistema,
  updateOpcao,
  executePipeline,
  getJobStatus,
  cancelExecution,
  getCredentials,
  saveCredentials,
  checkHealth,
} from '@/services/api'
import { mockConfig, mockSistemas, mockCredentials } from '../mocks/api'

describe('API Service', () => {
  const mockFetch = global.fetch as ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockFetch.mockClear()
  })

  // Helper para criar response mock
  function createFetchResponse(data: unknown, ok = true, status = 200) {
    return Promise.resolve({
      ok,
      status,
      statusText: ok ? 'OK' : 'Error',
      json: () => Promise.resolve(data),
    })
  }

  describe('getConfig', () => {
    it('fetches config from /api/config', async () => {
      mockFetch.mockReturnValue(createFetchResponse(mockConfig))

      const result = await getConfig()

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:4001/api/config',
        expect.objectContaining({
          headers: { 'Content-Type': 'application/json' },
        })
      )
      expect(result).toEqual(mockConfig)
    })

    it('throws error on HTTP error', async () => {
      mockFetch.mockReturnValue(createFetchResponse({}, false, 500))

      await expect(getConfig()).rejects.toThrow('HTTP 500')
    })
  })

  describe('saveConfig', () => {
    it('posts config to /api/config', async () => {
      mockFetch.mockReturnValue(createFetchResponse({ success: true }))

      await saveConfig(mockConfig)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:4001/api/config',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(mockConfig),
        })
      )
    })
  })

  describe('getSistemas', () => {
    it('fetches sistemas from /api/sistemas', async () => {
      mockFetch.mockReturnValue(createFetchResponse(mockSistemas))

      const result = await getSistemas()

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:4001/api/sistemas',
        expect.any(Object)
      )
      expect(result).toEqual(mockSistemas)
    })
  })

  describe('toggleSistema', () => {
    it('patches sistema toggle with query params', async () => {
      mockFetch.mockReturnValue(createFetchResponse({ success: true }))

      await toggleSistema('maps', true)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:4001/api/sistemas/maps/toggle?ativo=true',
        expect.objectContaining({ method: 'PATCH' })
      )
    })

    it('sends ativo=false when toggling off', async () => {
      mockFetch.mockReturnValue(createFetchResponse({ success: true }))

      await toggleSistema('fidc', false)

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('ativo=false'),
        expect.any(Object)
      )
    })
  })

  describe('updateOpcao', () => {
    it('patches opcao with query params', async () => {
      mockFetch.mockReturnValue(createFetchResponse({ success: true }))

      await updateOpcao('maps', 'excel', false)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:4001/api/sistemas/maps/opcao?opcao=excel&valor=false',
        expect.objectContaining({ method: 'PATCH' })
      )
    })
  })

  describe('executePipeline', () => {
    it('posts execution payload', async () => {
      mockFetch.mockReturnValue(createFetchResponse({ success: true, job_id: 1 }))

      const payload = {
        sistemas: ['maps', 'fidc'],
        limpar: false,
        opcoes: { maps: { excel: true } },
        data_inicial: '2024-01-01',
        data_final: '2024-01-31',
      }

      const result = await executePipeline(payload)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:4001/api/execute',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(payload),
        })
      )
      expect(result.job_id).toBe(1)
    })
  })

  describe('getJobStatus', () => {
    it('fetches job status by id', async () => {
      const jobData = { id: 1, status: 'completed' }
      mockFetch.mockReturnValue(createFetchResponse(jobData))

      const result = await getJobStatus(1)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:4001/api/jobs/1',
        expect.any(Object)
      )
      expect(result).toEqual(jobData)
    })
  })

  describe('cancelExecution', () => {
    it('posts cancel request', async () => {
      mockFetch.mockReturnValue(createFetchResponse({ success: true }))

      await cancelExecution('1')

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:4001/api/cancel/1',
        expect.objectContaining({ method: 'POST' })
      )
    })
  })

  describe('getCredentials', () => {
    it('fetches credentials', async () => {
      mockFetch.mockReturnValue(createFetchResponse(mockCredentials))

      const result = await getCredentials()

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:4001/api/credentials',
        expect.any(Object)
      )
      expect(result).toEqual(mockCredentials)
    })
  })

  describe('saveCredentials', () => {
    it('posts credentials', async () => {
      mockFetch.mockReturnValue(createFetchResponse({ success: true }))

      await saveCredentials(mockCredentials)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:4001/api/credentials',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(mockCredentials),
        })
      )
    })
  })

  describe('checkHealth', () => {
    it('fetches health status', async () => {
      const healthData = { status: 'ok', version: '2.0' }
      mockFetch.mockReturnValue(createFetchResponse(healthData))

      const result = await checkHealth()

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:4001/api/health',
        expect.any(Object)
      )
      expect(result).toEqual(healthData)
    })
  })

  describe('Error handling', () => {
    it('throws descriptive error on HTTP error', async () => {
      mockFetch.mockReturnValue(createFetchResponse({}, false, 404))

      await expect(getSistemas()).rejects.toThrow('HTTP 404')
    })

    it('handles timeout error', async () => {
      mockFetch.mockImplementation(() => {
        const error = new Error('Aborted')
        error.name = 'AbortError'
        return Promise.reject(error)
      })

      await expect(getConfig()).rejects.toThrow('Timeout')
    })

    it('handles network error', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'))

      await expect(getConfig()).rejects.toThrow('Network error')
    })
  })
})
