/**
 * Enhanced Service Worker with IndexedDB caching for offline support
 * Caches: Tasks, User Balance, Active Tasks, Completed Tasks
 */

importScripts('https://storage.googleapis.com/workbox-cdn/releases/6.4.1/workbox-sw.js');

// Database configuration
const DB_NAME = 'TaskStarsOfflineDB';
const DB_VERSION = 1;
const STORES = {
  TASKS: 'tasks',
  BALANCE: 'balance',
  ACTIVE_TASKS: 'activeTasks',
  COMPLETED_TASKS: 'completedTasks',
  REWARDS: 'rewards',
  PENDING_REQUESTS: 'pendingRequests'
};

// API routes to cache
const CACHE_ROUTES = [
  { pattern: /\/api\/v1\/tasks/, store: STORES.TASKS },
  { pattern: /\/api\/v1\/balance/, store: STORES.BALANCE },
  { pattern: /\/api\/v1\/user\/my-active/, store: STORES.ACTIVE_TASKS },
  { pattern: /\/api\/v1\/user\/my-completed/, store: STORES.COMPLETED_TASKS },
  { pattern: /\/api\/v1\/rewards/, store: STORES.REWARDS }
];

// Initialize IndexedDB
async function initDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      // Create object stores
      Object.values(STORES).forEach(storeName => {
        if (!db.objectStoreNames.contains(storeName)) {
          db.createObjectStore(storeName, { keyPath: 'id' });
        }
      });
    };
  });
}

// Cache API response to IndexedDB
async function cacheResponse(storeName, data, timestamp = Date.now()) {
  try {
    const db = await initDB();
    const transaction = db.transaction(storeName, 'readwrite');
    const store = transaction.objectStore(storeName);
    
    await store.put({
      id: 'cached',
      data: data,
      timestamp: timestamp
    });
    
    db.close();
  } catch (error) {
    console.error('[SW] Cache error:', error);
  }
}

// Get cached response from IndexedDB
async function getCachedResponse(storeName) {
  try {
    const db = await initDB();
    const transaction = db.transaction(storeName, 'readonly');
    const store = transaction.objectStore(storeName);
    
    const result = await store.get('cached');
    db.close();
    
    return result ? { data: result.data, timestamp: result.timestamp } : null;
  } catch (error) {
    console.error('[SW] Get cache error:', error);
    return null;
  }
}

// Clear cache for a specific store
async function clearCache(storeName) {
  try {
    const db = await initDB();
    const transaction = db.transaction(storeName, 'readwrite');
    const store = transaction.objectStore(storeName);
    await store.clear();
    db.close();
  } catch (error) {
    console.error('[SW] Clear cache error:', error);
  }
}

// Store pending request for later sync
async function storePendingRequest(method, url, body) {
  try {
    const db = await initDB();
    const transaction = db.transaction(STORES.PENDING_REQUESTS, 'readwrite');
    const store = transaction.objectStore(STORES.PENDING_REQUESTS);
    
    await store.add({
      method,
      url,
      body,
      timestamp: Date.now()
    });
    
    db.close();
  } catch (error) {
    console.error('[SW] Store pending request error:', error);
  }
}

// Workbox configuration
workbox.core.skipWaiting();
workbox.core.clientsClaim();

// Cache static assets
workbox.routing.registerRoute(
  ({ request }) => request.destination === 'image' || 
                  request.destination === 'script' || 
                  request.destination === 'style' ||
                  request.destination === 'font',
  new workbox.strategies.CacheFirst({
    cacheName: 'static-assets',
    plugins: [
      new workbox.expiration.ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 30 * 24 * 60 * 60 // 30 days
      })
    ]
  })
);

// API routes with IndexedDB caching
CACHE_ROUTES.forEach(({ pattern, store }) => {
  workbox.routing.registerRoute(
    pattern,
    async ({ url, request }) => {
      const storeInfo = CACHE_ROUTES.find(r => r.pattern.test(url.pathname));
      
      // Try network first
      try {
        const response = await fetch(request.clone());
        
        if (response.ok) {
          const data = await response.clone().json();
          await cacheResponse(storeInfo.store, data);
        }
        
        return response;
      } catch (error) {
        // Network failed - return cached data
        console.log('[SW] Network failed, serving from cache:', url.pathname);
        
        const cached = await getCachedResponse(storeInfo.store);
        
        if (cached) {
          const age = Date.now() - cached.timestamp;
          const ageMinutes = Math.floor(age / 60000);
          
          return new Response(JSON.stringify(cached.data), {
            status: 200,
            statusText: 'OK',
            headers: {
              'Content-Type': 'application/json',
              'X-Cache-Status': 'HIT',
              'X-Cache-Age': `${ageMinutes}m`
            }
          });
        }
        
        // No cache available
        return new Response(JSON.stringify({ 
          error: 'Offline and no cached data available' 
        }), {
          status: 503,
          statusText: 'Service Unavailable',
          headers: { 'Content-Type': 'application/json' }
        });
      }
    },
    'GET'
  );
});

// Handle POST/PUT/DELETE for offline queue
workbox.routing.registerRoute(
  ({ url }) => CACHE_ROUTES.some(r => r.pattern.test(url.pathname)),
  async ({ url, request }) => {
    try {
      return await fetch(request);
    } catch (error) {
      // Store for later sync
      const body = await request.clone().text().catch(() => null);
      await storePendingRequest(request.method, url.href, body);
      
      // Notify user about offline mode
      self.clients.matchAll().then(clients => {
        clients.forEach(client => {
          client.postMessage({
            type: 'OFFLINE_ACTION_QUEUED',
            method: request.method,
            url: url.pathname
          });
        });
      });
      
      return new Response(JSON.stringify({ 
        queued: true,
        message: 'Request queued for sync when online' 
      }), {
        status: 202,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  },
  ['POST', 'PUT', 'DELETE']
);

// Background sync when connection restored
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-pending-requests') {
    event.waitUntil(syncPendingRequests());
  }
});

async function syncPendingRequests() {
  try {
    const db = await initDB();
    const transaction = db.transaction(STORES.PENDING_REQUESTS, 'readonly');
    const store = transaction.objectStore(STORES.PENDING_REQUESTS);
    
    const requests = await store.getAll();
    db.close();
    
    for (const req of requests) {
      try {
        await fetch(req.url, {
          method: req.method,
          headers: { 'Content-Type': 'application/json' },
          body: req.body
        });
        
        // Remove from queue after successful sync
        const db2 = await initDB();
        const tx = db2.transaction(STORES.PENDING_REQUESTS, 'readwrite');
        await tx.objectStore(STORES.PENDING_REQUESTS).delete(req.id);
        db2.close();
      } catch (error) {
        console.error('[SW] Sync failed for request:', req.url);
      }
    }
    
    // Notify clients
    self.clients.matchAll().then(clients => {
      clients.forEach(client => {
        client.postMessage({ type: 'SYNC_COMPLETE' });
      });
    });
  } catch (error) {
    console.error('[SW] Sync error:', error);
  }
}

// Listen for messages from clients
self.addEventListener('message', (event) => {
  if (event.data.type === 'CLEAR_CACHE') {
    const storeName = event.data.store;
    if (storeName && STORES[storeName.toUpperCase()]) {
      clearCache(STORES[storeName.toUpperCase()]);
    } else {
      // Clear all caches
      Object.values(STORES).forEach(clearCache);
    }
  }
  
  if (event.data.type === 'FORCE_SYNC') {
    syncPendingRequests();
  }
});

// Network status change handlers
self.addEventListener('online', () => {
  console.log('[SW] Connection restored, syncing...');
  syncPendingRequests();
});

console.log('[SW] TaskStars Offline Service Worker activated');
