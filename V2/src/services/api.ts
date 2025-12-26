/**
 * ETL API Service - TanStack Query integration
 */
import type { ConfiguracaoETL, Sistema, ApiResponse } from '@/types/etl';

const API_BASE = 'http://localhost:4001/api';
const DEFAULT_TIMEOUT = 5000;

// Base request function with timeout
async function request<T>(
    endpoint: string,
    options: RequestInit = {},
    timeoutMs: number = DEFAULT_TIMEOUT
): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
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
            throw new Error('Timeout: servidor não respondeu');
        }
        throw error;
    }
}

// ==================== CONFIG ====================

export async function getConfig(): Promise<ConfiguracaoETL> {
    return request<ConfiguracaoETL>('/config');
}

export async function saveConfig(config: ConfiguracaoETL): Promise<ApiResponse> {
    return request<ApiResponse>('/config', {
        method: 'POST',
        body: JSON.stringify(config),
    });
}

// ==================== SISTEMAS ====================

export async function getSistemas(): Promise<Record<string, Sistema>> {
    return request<Record<string, Sistema>>('/sistemas');
}

export async function toggleSistema(id: string, ativo: boolean): Promise<ApiResponse> {
    return request<ApiResponse>(
        `/sistemas/${id}/toggle?ativo=${ativo}`,
        { method: 'PATCH' }
    );
}

export async function updateOpcao(
    id: string,
    opcao: string,
    valor: boolean
): Promise<ApiResponse> {
    return request<ApiResponse>(
        `/sistemas/${id}/opcao?opcao=${opcao}&valor=${valor}`,
        { method: 'PATCH' }
    );
}

// ==================== EXECUCAO ====================

export interface ExecutionPayload {
    sistemas: string[];
    limpar: boolean;
    opcoes: Record<string, Record<string, boolean>>;
    data_inicial?: string | null;
    data_final?: string | null;
}


export async function executePipeline(payload: ExecutionPayload): Promise<ApiResponse & { job_id?: number }> {
    return request<ApiResponse & { job_id?: number }>('/execute', {
        method: 'POST',
        body: JSON.stringify(payload)
    });
}

export async function getJobStatus(jobId: number): Promise<any> {
    return request<any>(`/jobs/${jobId}`);
}

export async function cancelExecution(id: string): Promise<ApiResponse> {
    return request<ApiResponse>(`/cancel/${id}`, { method: 'POST' });
}


// ==================== CREDENTIALS ====================

export async function getCredentials(): Promise<any> {
    return request<any>('/credentials');
}

export async function saveCredentials(credentials: any): Promise<ApiResponse> {
    return request<ApiResponse>('/credentials', {
        method: 'POST',
        body: JSON.stringify(credentials),
    });
}

// ==================== HEALTH ====================

export async function checkHealth(): Promise<{ status: string; version: string }> {
    return request('/health');
}

// Export all as api object for convenience
export const api = {
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
};

export default api;
