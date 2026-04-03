'use client';

import { useEffect, useRef, useCallback } from 'react';
import { WebSocketClient, WebSocketMessage, WebSocketEventHandler } from '@/services/websocket';

export function useWebSocket(token: string | null) {
  const wsRef = useRef<WebSocketClient | null>(null);

  useEffect(() => {
    if (!token) return;

    const ws = new WebSocketClient(token);
    ws.connect();
    wsRef.current = ws;

    return () => {
      ws.disconnect();
      wsRef.current = null;
    };
  }, [token]);

  const on = useCallback((event: string, handler: WebSocketEventHandler) => {
    wsRef.current?.on(event, handler);
    return () => wsRef.current?.off(event, handler);
  }, []);

  const send = useCallback((message: WebSocketMessage) => {
    wsRef.current?.send(message);
  }, []);

  return { on, send, isConnected: !!wsRef.current };
}
