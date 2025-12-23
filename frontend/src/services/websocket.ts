/**
 * WebSocket Service - Comunicacao em tempo real
 */
import { Client } from '@stomp/stompjs';
import SockJS from 'sockjs-client';
import type { LogEntry, StatusUpdate } from '../types';

type LogCallback = (log: LogEntry) => void;
type StatusCallback = (sistemaId: string, status: StatusUpdate) => void;

class WebSocketService {
  private client: Client | null = null;
  private logCallbacks: LogCallback[] = [];
  private statusCallbacks: StatusCallback[] = [];
  private connected = false;

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.client = new Client({
        webSocketFactory: () => new SockJS('/ws'),
        onConnect: () => {
          console.log('WebSocket conectado');
          this.connected = true;
          this.subscribeToTopics();
          resolve();
        },
        onDisconnect: () => {
          console.log('WebSocket desconectado');
          this.connected = false;
        },
        onStompError: (frame) => {
          console.error('Erro STOMP:', frame);
          reject(new Error(frame.headers['message']));
        },
      });

      this.client.activate();
    });
  }

  disconnect(): void {
    if (this.client) {
      this.client.deactivate();
      this.client = null;
      this.connected = false;
    }
  }

  private subscribeToTopics(): void {
    if (!this.client) return;

    // Subscribe to logs
    this.client.subscribe('/topic/logs', (message) => {
      const log: LogEntry = JSON.parse(message.body);
      this.logCallbacks.forEach((cb) => cb(log));
    });

    // Subscribe to status updates (pattern matching not supported, use specific)
    // We'll handle this by subscribing to individual systems
  }

  subscribeToSistemaStatus(sistemaId: string): void {
    if (!this.client || !this.connected) return;

    this.client.subscribe(`/topic/status/${sistemaId}`, (message) => {
      const status: StatusUpdate = JSON.parse(message.body);
      this.statusCallbacks.forEach((cb) => cb(sistemaId, status));
    });
  }

  onLog(callback: LogCallback): () => void {
    this.logCallbacks.push(callback);
    return () => {
      const index = this.logCallbacks.indexOf(callback);
      if (index > -1) {
        this.logCallbacks.splice(index, 1);
      }
    };
  }

  onStatusUpdate(callback: StatusCallback): () => void {
    this.statusCallbacks.push(callback);
    return () => {
      const index = this.statusCallbacks.indexOf(callback);
      if (index > -1) {
        this.statusCallbacks.splice(index, 1);
      }
    };
  }

  isConnected(): boolean {
    return this.connected;
  }
}

export const ws = new WebSocketService();
export default ws;
