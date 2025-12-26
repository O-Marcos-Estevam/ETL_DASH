/**
 * ETL Dashboard V2 - TypeScript Types
 */

export interface Credenciais {
    url: string;
    username: string;
    password: string;
}

export interface Fundo {
    nome: string;
    sigla?: string;
    tipo?: string;
    cnpj?: string;
    ativo: boolean;
}

export type StatusExecucao = 'IDLE' | 'RUNNING' | 'SUCCESS' | 'ERROR' | 'CANCELLED';

export interface Sistema {
    id: string;
    nome: string;
    descricao: string;
    icone: string;
    ativo: boolean;
    ordem: number;
    script?: string;
    funcao?: string;
    opcoes?: Record<string, boolean>;
    fundos?: Fundo[];
    status?: StatusExecucao;
    progresso?: number;
    mensagem?: string;
}

export interface Periodo {
    dataInicial: string | null;
    dataFinal: string | null;
    usarD1Anbima: boolean;
}

export interface ConfiguracaoETL {
    versao: string;
    ultimaModificacao: string;
    periodo: Periodo;
    sistemas: Record<string, Sistema>;
}

export interface LogEntry {
    level: 'INFO' | 'SUCCESS' | 'WARN' | 'ERROR';
    sistema: string;
    mensagem: string;
    timestamp: string;
}

export interface StatusUpdate {
    status: StatusExecucao;
    progresso: number;
    mensagem: string;
}

export interface ApiResponse<T = unknown> {
    success: boolean;
    status?: string;
    data?: T;
    error?: string;
    message?: string;
}

// Option display mappings
export const OPTION_ICONS: Record<string, string> = {
    pdf: '📄', csv: '📊', excel: '📗', xlsx: '📗', xml: '📋',
    pdf_lote: '📄📄', excel_lote: '📗📗', xml_lote: '📋📋',
    ativo: '📈', passivo: '📉', base_total: '🗄️'
};

export const OPTION_LABELS: Record<string, string> = {
    pdf: 'PDF', csv: 'CSV', excel: 'Excel', xlsx: 'Excel', xml: 'XML',
    pdf_lote: 'PDF Lote', excel_lote: 'Excel Lote', xml_lote: 'XML Lote',
    ativo: 'Ativo', passivo: 'Passivo', base_total: 'Base Total'
};
