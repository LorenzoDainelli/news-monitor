/* MyMoney PWA — service worker (v2 Fase 2).
   Mette in cache il "guscio" (shell) così l'app si apre anche offline.
   Strategia: cache-first per il guscio; l'API (/api/...) passa sempre dalla rete
   (non ha senso servirla dalla cache). Cambiare CACHE per forzare l'aggiornamento. */
var CACHE = "mymoney-shell-v9";
var ASSETS = [
  "./", "./index.html", "./styles.css", "./app.js", "./db.js", "./finance.js",
  "./sync.js", "./drive.js", "./manifest.webmanifest",
  "./icons/icon-192.png", "./icons/icon-512.png",
  "./icons/icon-maskable-512.png", "./icons/apple-touch-icon.png"
];

/* iOS/WebKit rifiuta una navigazione se il service worker restituisce una
   risposta che ha attraversato un redirect ("Response served by service worker
   has redirections"). Cloudflare Pages fa 308 /index.html -> /, quindi una
   risposta "redirected" può facilmente finire in cache o tornare dalla rete:
   qui la ricostruiamo pulita (stesso corpo, stessi header, senza flag redirect). */
function senzaRedirect(resp) {
  if (resp && resp.redirected) {
    return new Response(resp.body, {
      status: resp.status, statusText: resp.statusText, headers: resp.headers
    });
  }
  return resp;
}

self.addEventListener("install", function (e) {
  // Ogni asset viene PRIMA ripulito dai redirect e POI messo in cache: così un
  // 308 di Cloudflare non lascia una risposta "redirected" nel guscio (che poi
  // romperebbe la navigazione su iOS). Tollerante: un file mancante non blocca
  // l'installazione, si riprenderà dalla rete.
  e.waitUntil(
    caches.open(CACHE).then(function (c) {
      return Promise.all(ASSETS.map(function (u) {
        return fetch(u, { cache: "reload" }).then(function (resp) {
          if (resp && resp.ok) return c.put(u, senzaRedirect(resp));
        }).catch(function () {});
      }));
    }).then(function () { return self.skipWaiting(); })
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
  if (url.origin !== self.location.origin) return;            // Drive/Google: sempre rete
  if (url.pathname.indexOf("/api/") !== -1) return;           // API: lascia la rete
  if (e.request.mode === "navigate") {                         // pagina: guscio offline
    // Serviamo il guscio dalla cache (ripulito per sicurezza); se manca, la
    // radice "./" (che Cloudflare serve 200, senza redirect); infine la rete.
    e.respondWith(
      caches.match("./index.html").then(function (r) {
        if (r) return senzaRedirect(r);
        return caches.match("./").then(function (r2) {
          if (r2) return senzaRedirect(r2);
          return fetch("./").then(senzaRedirect);
        });
      })
    );
    return;
  }
  e.respondWith(caches.match(e.request).then(function (r) {
    return r || fetch(e.request).then(senzaRedirect);
  }));
});
