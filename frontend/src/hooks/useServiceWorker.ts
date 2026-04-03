'use client';

import { useEffect } from 'react';

export function useServiceWorker() {
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
}

// Helper to clear specific cache or all caches
export async function clearOfflineCache(store?: string) {
  if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
    navigator.serviceWorker.controller.postMessage({
      type: 'CLEAR_CACHE',
      store
    });
  }
}

// Force sync pending requests
export async function forceSync() {
  if ('serviceWorker' in navigator) {
    const registration = await navigator.serviceWorker.ready;
    
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({
        type: 'FORCE_SYNC'
      });
    }
    
    // Also trigger background sync if available
    if ('sync' in registration) {
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        await (registration as any).sync.register('sync-pending-requests');
      } catch (error) {
        console.error('[SW] Background sync registration failed:', error);
      }
    }
  }
}
