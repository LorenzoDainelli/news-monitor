/* MyMoney PWA — service worker (v2 Fase 2).
   Mette in cache il "guscio" (shell) così l'app si apre anche offline.
   Strategia: cache-first per il guscio; l'API (/api/...) passa sempre dalla rete
   (non ha senso servirla dalla cache). Cambiare CACHE per forzare l'aggiornamento. */
var CACHE = "mymoney-shell-v5";
var ASSETS = [
  "./", "./index.html", "./styles.css", "./app.js", "./db.js", "./finance.js",
  "./sync.js", "./manifest.webmanifest",
  "./icons/icon-192.png", "./icons/icon-512.png",
  "./icons/icon-maskable-512.png", "./icons/apple-touch-icon.png"
];

self.addEventListener("install", function (e) {
  e.waitUntil(
    caches.open(CACHE).then(function (c) { return c.addAll(ASSETS); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) { return k !== CACHE; })
        .map(function (k) { return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function (e) {
  var url = new URL(e.request.url);
  if (url.pathname.indexOf("/api/") !== -1) return;           // API: lascia la rete
  if (e.request.mode === "navigate") {                         // pagina: guscio offline
    e.respondWith(caches.match("./index.html").then(function (r) { return r || fetch(e.request); }));
    return;
  }
  e.respondWith(caches.match(e.request).then(function (r) { return r || fetch(e.request); }));
});
