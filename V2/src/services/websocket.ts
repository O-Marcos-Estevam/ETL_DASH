/**
 * WebSocket Service - Real-time logs and status updates
 */
import type { LogEntry, StatusUpdate } from '@/types/etl';

// Extended log entry with job_id from backend
export interface WSLogEntry extends LogEntry {
    job_id?: number;
}

// Job complete payload
export interface JobCompletePayload {
    job_id: number;
    status: string;
    duracao_segundos: number;
}

type LogHandler = (log: WSLogEntry) => void;
type StatusHandler = (sistemaId: string, status: StatusUpdate) => void;
type ConnectionHandler = (connected: boolean) => void;
type JobCompleteHandler = (payload: JobCompletePayload) => void;

class WebSocketService {
    private ws: WebSocket | null = null;
    private logHandlers: LogHandler[] = [];
    private statusHandlers: StatusHandler[] = [];
    private connectionHandlers: ConnectionHandler[] = [];
    private jobCompleteHandlers: JobCompleteHandler[] = [];
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 10;
    private reconnectDelay = 2000;
    private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    connect(): Promise<void> {
        return new Promise((resolve, reject) => {
            // Clear any existing reconnect timer
            if (this.reconnectTimer) {
                clearTimeout(this.reconnectTimer);
                this.reconnectTimer = null;
            }

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.hostname}:4001/ws`;

            try {
                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    console.log('[WS] Connected to', wsUrl);
                    this.reconnectAttempts = 0;
                    this.notifyConnectionChange(true);
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        this.handleMessage(data);
                    } catch (e) {
                        console.warn('[WS] Failed to parse message:', e);
                    }
                };

                this.ws.onclose = (event) => {
                    console.log('[WS] Disconnected', event.code, event.reason);
                    this.notifyConnectionChange(false);
                    this.attemptReconnect();
                };

                this.ws.onerror = (error) => {
                    console.error('[WS] Error:', error);
                    // Don't reject here - let onclose handle reconnection
                };

                // Timeout for initial connection
                setTimeout(() => {
                    if (this.ws?.readyState !== WebSocket.OPEN) {
                        reject(new Error('Connection timeout'));
                    }
                }, 5000);

            } catch (error) {
                reject(error);
            }
        });
    }

    private handleMessage(data: any): void {
        const { type, payload } = data;

        if (!type || !payload) {
            console.warn('[WS] Invalid message format:', data);
            return;
        }

        switch (type) {
            case 'log':
                // payload: { level, sistema, mensagem, timestamp, job_id? }
                this.logHandlers.forEach(handler => handler(payload as WSLogEntry));
                break;

            case 'status':
                // payload: { sistema_id, status, progresso, mensagem }
                if (payload.sistema_id) {
                    const statusUpdate: StatusUpdate = {
                        status: payload.status,
                        progresso: payload.progresso || 0,
                        mensagem: payload.mensagem || ''
                    };
                    this.statusHandlers.forEach(handler =>
                        handler(payload.sistema_id, statusUpdate)
                    );
                }
                break;

            case 'job_complete':
                // payload: { job_id, status, duracao_segundos }
                this.jobCompleteHandlers.forEach(handler =>
                    handler(payload as JobCompletePayload)
                );
                break;

            default:
                console.log('[WS] Unknown message type:', type);
        }
    }

    private attemptReconnect(): void {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(this.reconnectDelay * this.reconnectAttempts, 30000);
            console.log(`[WS] Reconnecting in ${delay}ms... attempt ${this.reconnectAttempts}`);

            this.reconnectTimer = setTimeout(() => {
                this.connect().catch((err) => {
                    console.warn('[WS] Reconnect failed:', err);
                });
            }, delay);
        } else {
            console.error('[WS] Max reconnection attempts reached');
        }
    }

    private notifyConnectionChange(connected: boolean): void {
        this.connectionHandlers.forEach(handler => handler(connected));
    }

    disconnect(): void {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        this.reconnectAttempts = this.maxReconnectAttempts; // Prevent auto-reconnect
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    isConnected(): boolean {
        return this.ws?.readyState === WebSocket.OPEN;
    }

    // Reset reconnect counter (call when user triggers manual reconnect)
    resetReconnect(): void {
        this.reconnectAttempts = 0;
    }

    // Event subscriptions
    onLog(handler: LogHandler): () => void {
        this.logHandlers.push(handler);
        return () => {
            this.logHandlers = this.logHandlers.filter(h => h !== handler);
        };
    }

    onStatusUpdate(handler: StatusHandler): () => void {
        this.statusHandlers.push(handler);
        return () => {
            this.statusHandlers = this.statusHandlers.filter(h => h !== handler);
        };
    }

    onConnectionChange(handler: ConnectionHandler): () => void {
        this.connectionHandlers.push(handler);
        return () => {
            this.connectionHandlers = this.connectionHandlers.filter(h => h !== handler);
        };
    }

    onJobComplete(handler: JobCompleteHandler): () => void {
        this.jobCompleteHandlers.push(handler);
        return () => {
            this.jobCompleteHandlers = this.jobCompleteHandlers.filter(h => h !== handler);
        };
    }
}

export const ws = new WebSocketService();
export default ws;
