/**
 * FinanceiroMax - Service Worker
 * Provides offline functionality and caching for PWA
 */

const CACHE_NAME = 'financeiro-max-v1.0.0';
const STATIC_CACHE = 'static-cache-v1';
const DYNAMIC_CACHE = 'dynamic-cache-v1';

// Assets to cache
const STATIC_ASSETS = [
    '/',
    '/auth/login',
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/manifest.json',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://cdn.jsdelivr.net/npm/chart.js'
];

// API routes to cache
const API_ROUTES = [
    '/clients',
    '/receivables',
    '/payables',
    '/sales',
    '/whatsapp'
];

// Install event - cache static assets
self.addEventListener('install', event => {
    console.log('Service Worker: Installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('Service Worker: Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .catch(error => {
                console.error('Service Worker: Error caching static assets', error);
            })
    );
    
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Service Worker: Activating...');
    
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cache => {
                    if (cache !== STATIC_CACHE && cache !== DYNAMIC_CACHE) {
                        console.log('Service Worker: Clearing old cache', cache);
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
    
    self.clients.claim();
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', event => {
    const { request } = event;
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Skip chrome-extension requests
    if (request.url.startsWith('chrome-extension://')) {
        return;
    }
    
    event.respondWith(
        handleFetch(request)
    );
});

async function handleFetch(request) {
    const url = new URL(request.url);
    
    try {
        // Try network first for API calls
        if (isApiRequest(url)) {
            return await handleApiRequest(request);
        }
        
        // Try cache first for static assets
        if (isStaticAsset(url)) {
            return await handleStaticAsset(request);
        }
        
        // Default: network first, then cache
        return await handleDefault(request);
        
    } catch (error) {
        console.error('Service Worker: Fetch error', error);
        return await handleOffline(request);
    }
}

async function handleApiRequest(request) {
    try {
        // Try network first
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Cache successful responses
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
            return networkResponse;
        }
        
        throw new Error('Network request failed');
        
    } catch (error) {
        // Fallback to cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            console.log('Service Worker: Serving API from cache', request.url);
            return cachedResponse;
        }
        
        // Return offline page or error response
        return new Response(
            JSON.stringify({
                error: 'Offline',
                message: 'Esta funcionalidade não está disponível offline'
            }),
            {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}

async function handleStaticAsset(request) {
    // Try cache first
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }
    
    // Try network if not in cache
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Cache the response
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, networkResponse.clone());
            return networkResponse;
        }
        
        throw new Error('Network request failed');
        
    } catch (error) {
        // Return fallback for failed static assets
        return new Response('Asset not available offline', {
            status: 503,
            headers: { 'Content-Type': 'text/plain' }
        });
    }
}

async function handleDefault(request) {
    try {
        // Try network first
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Cache successful responses
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
            return networkResponse;
        }
        
        throw new Error('Network request failed');
        
    } catch (error) {
        // Try cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline page
        return await handleOffline(request);
    }
}

async function handleOffline(request) {
    const url = new URL(request.url);
    
    // Return cached home page for navigation requests
    if (request.mode === 'navigate') {
        const cachedResponse = await caches.match('/');
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return minimal offline page
        return new Response(`
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Offline - FinanceiroMax</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        min-height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        text-align: center;
                    }
                    .container {
                        max-width: 500px;
                        padding: 2rem;
                    }
                    .icon {
                        font-size: 4rem;
                        margin-bottom: 1rem;
                        opacity: 0.8;
                    }
                    h1 {
                        margin-bottom: 1rem;
                        font-weight: 300;
                    }
                    p {
                        opacity: 0.9;
                        line-height: 1.6;
                    }
                    .btn {
                        background: rgba(255, 255, 255, 0.2);
                        border: 2px solid rgba(255, 255, 255, 0.3);
                        color: white;
                        padding: 0.75rem 1.5rem;
                        border-radius: 0.5rem;
                        text-decoration: none;
                        display: inline-block;
                        margin-top: 1rem;
                        transition: all 0.3s ease;
                    }
                    .btn:hover {
                        background: rgba(255, 255, 255, 0.3);
                        border-color: rgba(255, 255, 255, 0.5);
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="icon">📱</div>
                    <h1>Você está offline</h1>
                    <p>
                        Não foi possível conectar ao FinanceiroMax. 
                        Verifique sua conexão com a internet e tente novamente.
                    </p>
                    <a href="/" class="btn" onclick="window.location.reload()">
                        Tentar Novamente
                    </a>
                </div>
            </body>
            </html>
        `, {
            status: 503,
            headers: { 'Content-Type': 'text/html; charset=utf-8' }
        });
    }
    
    // Return error response for other requests
    return new Response('Offline', { status: 503 });
}

// Helper functions
function isApiRequest(url) {
    return API_ROUTES.some(route => url.pathname.startsWith(route)) ||
           url.pathname.startsWith('/api/');
}

function isStaticAsset(url) {
    return url.pathname.startsWith('/static/') ||
           url.hostname !== self.location.hostname ||
           STATIC_ASSETS.includes(url.href);
}

// Background sync for offline form submissions
self.addEventListener('sync', event => {
    console.log('Service Worker: Background sync', event.tag);
    
    if (event.tag === 'form-submission') {
        event.waitUntil(syncFormSubmissions());
    }
});

async function syncFormSubmissions() {
    try {
        // Get pending form submissions from IndexedDB
        const submissions = await getPendingSubmissions();
        
        for (const submission of submissions) {
            try {
                const response = await fetch(submission.url, {
                    method: submission.method,
                    headers: submission.headers,
                    body: submission.body
                });
                
                if (response.ok) {
                    await removePendingSubmission(submission.id);
                    console.log('Service Worker: Form submission synced', submission.id);
                }
                
            } catch (error) {
                console.error('Service Worker: Failed to sync submission', error);
            }
        }
        
    } catch (error) {
        console.error('Service Worker: Background sync failed', error);
    }
}

// IndexedDB operations for offline form submissions
async function getPendingSubmissions() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('FinanceiroMax', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['submissions'], 'readonly');
            const store = transaction.objectStore('submissions');
            const getRequest = store.getAll();
            
            getRequest.onsuccess = () => resolve(getRequest.result);
            getRequest.onerror = () => reject(getRequest.error);
        };
        
        request.onupgradeneeded = () => {
            const db = request.result;
            if (!db.objectStoreNames.contains('submissions')) {
                const store = db.createObjectStore('submissions', { keyPath: 'id', autoIncrement: true });
                store.createIndex('timestamp', 'timestamp');
            }
        };
    });
}

async function removePendingSubmission(id) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('FinanceiroMax', 1);
        
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['submissions'], 'readwrite');
            const store = transaction.objectStore('submissions');
            const deleteRequest = store.delete(id);
            
            deleteRequest.onsuccess = () => resolve();
            deleteRequest.onerror = () => reject(deleteRequest.error);
        };
    });
}

// Push notifications
self.addEventListener('push', event => {
    console.log('Service Worker: Push notification received');
    
    const options = {
        body: 'Você tem uma nova notificação no FinanceiroMax',
        icon: '/static/manifest.json',
        badge: '/static/manifest.json',
        tag: 'financeiro-notification',
        requireInteraction: false,
        actions: [
            {
                action: 'view',
                title: 'Ver',
                icon: '/static/manifest.json'
            },
            {
                action: 'dismiss',
                title: 'Dispensar'
            }
        ]
    };
    
    if (event.data) {
        try {
            const data = event.data.json();
            options.body = data.body || options.body;
            options.title = data.title || 'FinanceiroMax';
            options.data = data;
        } catch (error) {
            console.error('Service Worker: Failed to parse push data', error);
        }
    }
    
    event.waitUntil(
        self.registration.showNotification('FinanceiroMax', options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', event => {
    console.log('Service Worker: Notification clicked');
    
    event.notification.close();
    
    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Message handler for communication with main thread
self.addEventListener('message', event => {
    console.log('Service Worker: Message received', event.data);
    
    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data.type === 'GET_VERSION') {
        event.ports[0].postMessage({
            type: 'VERSION',
            version: CACHE_NAME
        });
    }
});

console.log('Service Worker: Loaded successfully');
