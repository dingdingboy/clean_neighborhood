import { useEffect, useRef, useState, useCallback } from 'react';
import { ReportStatus } from '@/types';

interface WebSocketMessage {
  type: 'status' | 'status_update' | 'error' | 'pong';
  report_id?: number;
  status?: ReportStatus;
  updated_at?: string;
  progress_percent?: number;
  current_step?: string;
  message?: string;
}

interface UseWebSocketOptions {
  reportId: number | null;
  onStatusUpdate?: (status: ReportStatus, data?: Partial<WebSocketMessage>) => void;
  onError?: (message: string) => void;
  enabled?: boolean;
}

export function useWebSocket({
  reportId,
  onStatusUpdate,
  onError,
  enabled = true,
}: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (!reportId || !enabled) return;

    // Determine WebSocket URL based on current protocol
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/reports/${reportId}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        console.log(`WebSocket connected for report ${reportId}`);
      };

      ws.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(data);

          switch (data.type) {
            case 'status':
            case 'status_update':
              if (data.status && onStatusUpdate) {
                onStatusUpdate(data.status, data);
              }
              break;
            case 'error':
              if (onError && data.message) {
                onError(data.message);
              }
              break;
            case 'pong':
              // Heartbeat response, no action needed
              break;
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
        if (onError) {
          onError('WebSocket connection error');
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log(`WebSocket disconnected for report ${reportId}`);

        // Attempt to reconnect after 3 seconds
        if (enabled) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, 3000);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setIsConnected(false);
    }
  }, [reportId, enabled, onStatusUpdate, onError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  // Connect when reportId changes or enabled becomes true
  useEffect(() => {
    if (enabled && reportId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [reportId, enabled, connect, disconnect]);

  // Heartbeat to keep connection alive
  useEffect(() => {
    if (!isConnected) return;

    const heartbeat = setInterval(() => {
      sendMessage({ action: 'ping' });
    }, 30000); // Send ping every 30 seconds

    return () => {
      clearInterval(heartbeat);
    };
  }, [isConnected, sendMessage]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
  };
}
