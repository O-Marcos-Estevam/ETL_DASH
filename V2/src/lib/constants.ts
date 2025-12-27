/**
 * Constantes centralizadas do ETL Dashboard V2
 */

// API Configuration
export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:4001/api';
export const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:4001';

// Timeouts
export const DEFAULT_TIMEOUT = 5000; // 5 segundos
export const LONG_TIMEOUT = 30000; // 30 segundos

// Logs
export const MAX_LOGS = 1000;

// Sistemas disponíveis
export const SISTEMAS_IDS = [
  'amplis_reag',
  'amplis_master',
  'maps',
  'fidc',
  'jcot',
  'britech',
  'qore'
] as const;

export type SistemaId = typeof SISTEMAS_IDS[number];

// Status de execução
export const STATUS_EXECUCAO = {
  IDLE: 'IDLE',
  RUNNING: 'RUNNING',
  SUCCESS: 'SUCCESS',
  ERROR: 'ERROR',
  CANCELLED: 'CANCELLED',
} as const;

export type StatusExecucao = typeof STATUS_EXECUCAO[keyof typeof STATUS_EXECUCAO];

// Cores de status para UI
export const STATUS_COLORS = {
  IDLE: 'border-muted opacity-60',
  RUNNING: 'border-blue-500/50 bg-blue-500/5',
  SUCCESS: 'border-green-500/30 bg-green-500/5',
  ERROR: 'border-red-500/30 bg-red-500/5',
  CANCELLED: 'border-yellow-500/30 bg-yellow-500/5',
} as const;

// Log levels
export const LOG_LEVELS = {
  INFO: 'INFO',
  SUCCESS: 'SUCCESS',
  WARNING: 'WARNING',
  ERROR: 'ERROR',
  DEBUG: 'DEBUG',
} as const;

export type LogLevel = typeof LOG_LEVELS[keyof typeof LOG_LEVELS];

// LocalStorage keys
export const STORAGE_KEYS = {
  SIDEBAR_COLLAPSED: 'sidebar-collapsed',
  THEME: 'vite-ui-theme',
  CURRENT_JOB_ID: 'current_etl_job_id',
} as const;
