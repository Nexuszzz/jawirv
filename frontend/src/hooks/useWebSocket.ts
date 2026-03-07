/**
 * JAWIR OS — WebSocket Hook
 * Manages connection to ws://localhost:8000/ws/chat with auto-reconnect
 * Uses refs to avoid React 18 Strict Mode double-mount issues
 */

import { useCallback, useEffect, useRef } from 'react';
import type { WSMessage } from '@/types';

interface UseWebSocketOptions {
  url: string;
  onMessage: (data: WSMessage) => void;
  onConnectionChange: (connected: boolean) => void;
  reconnectInterval?: number;
}

export function useWebSocket({
  url,
  onMessage,
  onConnectionChange,
  reconnectInterval = 3000,
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isConnectingRef = useRef(false);
  const isMountedRef = useRef(false);

  // Keep callback refs updated to avoid stale closures
  const onMessageRef = useRef(onMessage);
  const onConnectionChangeRef = useRef(onConnectionChange);
  onMessageRef.current = onMessage;
  onConnectionChangeRef.current = onConnectionChange;

  const cleanup = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (pingTimerRef.current) {
      clearInterval(pingTimerRef.current);
      pingTimerRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    // Don't connect if unmounted (React Strict Mode cleanup)
    if (!isMountedRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN || isConnectingRef.current) return;

    cleanup();
    isConnectingRef.current = true;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('🔌 WebSocket connected');
        isConnectingRef.current = false;
        onConnectionChangeRef.current(true);

        // Start heartbeat ping every 25s
        pingTimerRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 25000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WSMessage;
          onMessageRef.current(data);
        } catch (err) {
          console.error('Failed to parse WS message:', err);
        }
      };

      ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        isConnectingRef.current = false;
        onConnectionChangeRef.current(false);
        cleanup();

        // Auto-reconnect only if still mounted
        if (isMountedRef.current) {
          reconnectTimerRef.current = setTimeout(() => {
            console.log('🔄 Reconnecting...');
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        isConnectingRef.current = false;
      };
    } catch {
      isConnectingRef.current = false;
      if (isMountedRef.current) {
        reconnectTimerRef.current = setTimeout(connect, reconnectInterval);
      }
    }
  }, [url, reconnectInterval, cleanup]);

  // Connect on mount
  useEffect(() => {
    isMountedRef.current = true;
    connect();
    return () => {
      isMountedRef.current = false;
      cleanup();
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const sendMessage = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
      return true;
    }
    console.warn('WebSocket not connected');
    return false;
  }, []);

  return { sendMessage };
}
