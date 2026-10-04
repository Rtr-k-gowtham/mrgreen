// MR.GREEN Service Worker - Static Asset Cache Only
const CACHE_NAME = 'mrgreen-static-v1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icons/icon.svg',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // STRICT RULE: NEVER cache API calls, AI chat responses, or WebSocket/streaming requests
  if (url.pathname.startsWith('/api') || url.pathname.startsWith('/health') || event.request.method !== 'GET') {
    return;
  }

  // Network-first for HTML, Cache-first for immutable static bundles (js, css, images, fonts)
  if (url.pathname.match(/\.(js|css|png|jpg|svg|woff2?|ttf|ico)$/)) {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const clone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return networkResponse;
        });
      })
    );
    return;
  }

  // Network-first for navigation requests with cache fallback
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request) || caches.match('/index.html'))
  );
});
