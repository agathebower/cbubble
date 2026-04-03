const CACHE_NAME = "cbubble-v1";
const STATIC_ASSETS = ["/", "/static/css/style.css", "/static/js/app.js", "/static/js/feed.js", "/static/js/popup.js"];
self.addEventListener("install", (e) => {
    e.waitUntil(caches.open(CACHE_NAME).then((c) => c.addAll(STATIC_ASSETS)));
    self.skipWaiting();
});
self.addEventListener("activate", (e) => {
    e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))));
    self.clients.claim();
});
self.addEventListener("fetch", (e) => {
    const url = new URL(e.request.url);
    if (url.pathname.startsWith("/api/")) {
        e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
    } else {
        e.respondWith(caches.match(e.request).then((c) => c || fetch(e.request)));
    }
});
