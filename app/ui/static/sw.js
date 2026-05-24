/**
 * Service Worker for Rosary Progress Tracker PWA.
 *
 * Strategy: cache the static shell (HTML, manifest, this SW) on install,
 * serve it from cache for instant loads, and always go to the network for
 * API requests (SSE stream, state mutations, transcripts).
 */

const CACHE_NAME   = 'rosary-v1';
const STATIC_SHELL = ['/', '/static/manifest.json'];

// API paths that must never be served from cache
const API_PREFIXES = ['/stream', '/transcript', '/advance', '/undo', '/reset', '/state', '/language'];

function isApiRequest(url) {
  const path = new URL(url).pathname;
  return API_PREFIXES.some(p => path.startsWith(p));
}

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(STATIC_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  // Remove old caches from previous versions
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const { request } = event;

  // Always network-only for API and SSE — never cache dynamic state
  if (isApiRequest(request.url)) return;

  // Cache-first for the static shell; network fallback updates cache
  event.respondWith(
    caches.match(request).then(cached => {
      const networkFetch = fetch(request).then(response => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(c => c.put(request, clone));
        }
        return response;
      });
      return cached || networkFetch;
    })
  );
});
