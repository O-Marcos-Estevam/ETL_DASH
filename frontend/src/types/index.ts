/**
 * ETL Dashboard V2 - TypeScript Types
 */

export interface Credenciais {
  url: string;
  usuario: string;
  senha: string;
}

export interface Fundo {
  nome: string;
  sigla?: string;
  tipo?: string;  // FIDC, FIP, FIM, FII
  cnpj?: string;
  ativo: boolean;
  observacao?: string;
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
  credenciais: Credenciais;
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

export interface ConfiguracaoEmail {
  ativo: boolean;
  enviarSucesso: boolean;
  enviarErro: boolean;
  destinatarios: string[];
  copia: string[];
}

export interface Opcoes {
  limparPastasAntes: boolean;
  confirmarLimpeza: boolean;
  pararEmErro: boolean;
}

export interface RegistroHistorico {
  timestamp: string;
  sistema: string;
  acao: string;
  status: string;
  detalhes?: string;
}

export interface ConfiguracaoETL {
  versao: string;
  ultimaModificacao: string;
  periodo: Periodo;
  caminhos: Record<string, string>;
  sistemas: Record<string, Sistema>;
  email: ConfiguracaoEmail;
  opcoes: Opcoes;
  historico: RegistroHistorico[];
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
  data?: T;
  error?: string;
  message?: string;
}

// Option icons and labels
export const OPTION_ICONS: Record<string, string> = {
  pdf: '📄',
  csv: '📊',
  excel: '📗',
  xlsx: '📗',
  xml: '📋',
  pdf_lote: '📄📄',
  excel_lote: '📗📗',
  xml_lote: '📋📋',
  ativo: '📈',
  passivo: '📉',
  base_total: '🗄️'
};

export const OPTION_LABELS: Record<string, string> = {
  pdf: 'PDF',
  csv: 'CSV',
  excel: 'Excel',
  xlsx: 'Excel',
  xml: 'XML',
  pdf_lote: 'PDF Lote',
  excel_lote: 'Excel Lote',
  xml_lote: 'XML Lote',
  ativo: 'Ativo',
  passivo: 'Passivo',
  base_total: 'Base Total'
};
