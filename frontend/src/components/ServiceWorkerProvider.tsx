'use client';

import { ReactNode, useEffect } from 'react';

export function ServiceWorkerProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker
        .register('/sw-offline.js')
        .then((registration) => {
          console.log('[SW] Registered:', registration.scope);
          
          // Check for updates
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            if (newWorker) {
              newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                  console.log('[SW] New version available');
                }
              });
            }
          });
        })
        .catch((error) => {
          console.error('[SW] Registration failed:', error);
        });
      
      // Listen for messages from SW
      navigator.serviceWorker.addEventListener('message', (event) => {
        if (event.data.type === 'OFFLINE_ACTION_QUEUED') {
          console.log('[SW] Action queued for sync:', event.data);
        }
        if (event.data.type === 'SYNC_COMPLETE') {
          console.log('[SW] Pending actions synced');
          // Refresh data
          window.location.reload();
        }
      });
    }
  }, []);

  return <>{children}</>;
}
