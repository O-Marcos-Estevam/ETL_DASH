/**
 * API Service - Comunicacao com o backend Java
 */
import type { ConfiguracaoETL, Sistema, ApiResponse } from '../types';

const API_BASE = '/api';

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    timeoutMs: number = 5000
  ): Promise<T> {
    const url = `${API_BASE}${endpoint}`;

    // Criar AbortController para timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Timeout: servidor não respondeu em tempo');
      }
      throw error;
    }
  }

  // ==================== CONFIG ====================

  async getConfig(): Promise<ConfiguracaoETL> {
    return this.request<ConfiguracaoETL>('/config');
  }

  async saveConfig(config: ConfiguracaoETL): Promise<ApiResponse> {
    return this.request<ApiResponse>('/config', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  // ==================== SISTEMAS ====================

  async getSistemas(): Promise<Record<string, Sistema>> {
    return this.request<Record<string, Sistema>>('/sistemas');
  }

  async getSistemasAtivos(): Promise<Record<string, Sistema>> {
    return this.request<Record<string, Sistema>>('/sistemas/ativos');
  }

  async getSistema(id: string): Promise<Sistema> {
    return this.request<Sistema>(`/sistemas/${id}`);
  }

  async toggleSistema(id: string, ativo: boolean): Promise<ApiResponse> {
    return this.request<ApiResponse>(
      `/sistemas/${id}/toggle?ativo=${ativo}`,
      { method: 'PATCH' }
    );
  }

  async updateOpcao(
    id: string,
    opcao: string,
    valor: boolean
  ): Promise<ApiResponse> {
    return this.request<ApiResponse>(
      `/sistemas/${id}/opcao?opcao=${opcao}&valor=${valor}`,
      { method: 'PATCH' }
    );
  }

  // ==================== EXECUCAO ====================

  async executePipeline(limparPastas: boolean = false): Promise<ApiResponse> {
    return this.request<ApiResponse>(`/execute?limparPastas=${limparPastas}`, { method: 'POST' });
  }

  async executeSistema(id: string): Promise<ApiResponse> {
    return this.request<ApiResponse>(`/execute/${id}`, { method: 'POST' });
  }

  async cancelExecution(id: string): Promise<ApiResponse> {
    return this.request<ApiResponse>(`/cancel/${id}`, { method: 'POST' });
  }

  // ==================== CREDENTIALS ====================

  async getCredentials(): Promise<any> {
    return this.request<any>('/credentials');
  }

  async saveCredentials(credentials: any): Promise<ApiResponse> {
    return this.request<ApiResponse>('/credentials', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  // ==================== HEALTH ====================

  async health(): Promise<{ status: string; version: string }> {
    return this.request('/health');
  }
}

export const api = new ApiService();
export default api;

