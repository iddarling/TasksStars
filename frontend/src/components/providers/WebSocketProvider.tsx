'use client';

import { useEffect } from 'react';
import { useUserStore } from '@/store/userStore';
import { useAppStore } from '@/store/appStore';

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated } = useUserStore();
  const { initWebSocket, disconnectWebSocket } = useAppStore();

  useEffect(() => {
    if (isAuthenticated && user) {
      const token = localStorage.getItem('access_token');
      if (token) {
        initWebSocket(token);
      }
    } else {
      disconnectWebSocket();
    }

    return () => {
      disconnectWebSocket();
    };
  }, [isAuthenticated, user, initWebSocket, disconnectWebSocket]);

  return <>{children}</>;
}
