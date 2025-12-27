import { useState, useCallback, useRef, useEffect } from 'react';

export type NotificationType = 'success' | 'error' | 'warning' | 'info';

export interface Notification {
  id: string;
  message: string;
  type: NotificationType;
  duration?: number;
}

interface UseNotificationReturn {
  notification: Notification | null;
  showNotification: (message: string, type?: NotificationType, duration?: number) => void;
  hideNotification: () => void;
  success: (message: string, duration?: number) => void;
  error: (message: string, duration?: number) => void;
  warning: (message: string, duration?: number) => void;
  info: (message: string, duration?: number) => void;
}

const DEFAULT_DURATION = 4000;

/**
 * Hook para gerenciar notificações/toasts
 *
 * @returns Objeto com estado e funções de notificação
 */
export function useNotification(): UseNotificationReturn {
  const [notification, setNotification] = useState<Notification | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Limpa timeout ao desmontar
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const hideNotification = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setNotification(null);
  }, []);

  const showNotification = useCallback((
    message: string,
    type: NotificationType = 'info',
    duration: number = DEFAULT_DURATION
  ) => {
    // Limpa notificação anterior
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    const id = `notification-${Date.now()}`;
    setNotification({ id, message, type, duration });

    // Auto-hide
    if (duration > 0) {
      timeoutRef.current = setTimeout(() => {
        setNotification(null);
      }, duration);
    }
  }, []);

  const success = useCallback((message: string, duration?: number) => {
    showNotification(message, 'success', duration);
  }, [showNotification]);

  const error = useCallback((message: string, duration?: number) => {
    showNotification(message, 'error', duration);
  }, [showNotification]);

  const warning = useCallback((message: string, duration?: number) => {
    showNotification(message, 'warning', duration);
  }, [showNotification]);

  const info = useCallback((message: string, duration?: number) => {
    showNotification(message, 'info', duration);
  }, [showNotification]);

  return {
    notification,
    showNotification,
    hideNotification,
    success,
    error,
    warning,
    info,
  };
}
