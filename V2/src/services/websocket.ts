/**
 * WebSocket Service - Real-time logs and status updates
 */
import type { LogEntry, StatusUpdate } from '@/types/etl';

type LogHandler = (log: LogEntry) => void;
type StatusHandler = (sistemaId: string, status: StatusUpdate) => void;
type ConnectionHandler = (connected: boolean) => void;

class WebSocketService {
    private ws: WebSocket | null = null;
    private logHandlers: LogHandler[] = [];
    private statusHandlers: StatusHandler[] = [];
    private connectionHandlers: ConnectionHandler[] = [];
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 2000;

    connect(): Promise<void> {
        return new Promise((resolve, reject) => {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.hostname}:4001/ws`;

            try {
                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    console.log('[WS] Connected');
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

                this.ws.onclose = () => {
                    console.log('[WS] Disconnected');
                    this.notifyConnectionChange(false);
                    this.attemptReconnect();
                };

                this.ws.onerror = (error) => {
                    console.error('[WS] Error:', error);
                    reject(error);
                };

            } catch (error) {
                reject(error);
            }
        });
    }

    private handleMessage(data: any): void {
        if (data.type === 'log' && data.payload) {
            this.logHandlers.forEach(handler => handler(data.payload as LogEntry));
        } else if (data.type === 'status' && data.sistemaId && data.payload) {
            this.statusHandlers.forEach(handler =>
                handler(data.sistemaId, data.payload as StatusUpdate)
            );
        }
    }

    private attemptReconnect(): void {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`[WS] Reconnecting... attempt ${this.reconnectAttempts}`);
            setTimeout(() => this.connect().catch(() => { }), this.reconnectDelay);
        }
    }

    private notifyConnectionChange(connected: boolean): void {
        this.connectionHandlers.forEach(handler => handler(connected));
    }

    disconnect(): void {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    isConnected(): boolean {
        return this.ws?.readyState === WebSocket.OPEN;
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

    // Subscribe to system status
    subscribeToSistemaStatus(sistemaId: string): void {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                action: 'subscribe',
                sistemaId,
            }));
        }
    }
}

export const ws = new WebSocketService();
export default ws;
