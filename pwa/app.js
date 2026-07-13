/* MyMoney PWA — guscio (v2 Fase 2).
   - registra il service worker (apertura offline);
   - se raggiunge l'API del PC (/api/finanze/stato) mostra i portafogli reali
     (utile in locale/LAN); altrimenti mostra lo stato "ancora nessun dato",
     perché sul telefono i dati arriveranno dalla copia locale + sync (Fasi 3-4);
   - indicatore online/offline e suggerimento d'installazione su iPhone. */
(function () {
  "use strict";
  var lang = "it";
  var eur = function (n) {
    return "€ " + Number(n).toLocaleString(lang, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };
  var $ = function (id) { return document.getElementById(id); };

  // ---- service worker ----
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("sw.js").catch(function () {/* offline la 1a volta va bene */});
    });
  }

  // ---- stato rete ----
  function segnalaRete() {
    var on = navigator.onLine;
    $("net").textContent = on ? "online" : "offline";
    $("dot").className = "dot " + (on ? "online" : "offline");
  }
  window.addEventListener("online", segnalaRete);
  window.addEventListener("offline", segnalaRete);
  segnalaRete();

  // ---- suggerimento installazione (iOS Safari, non ancora installata) ----
  var isStandalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
  var isiOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
  if (isiOS && !isStandalone) { $("install-hint").hidden = false; }

  // ---- prova a leggere lo stato dall'API del PC (se raggiungibile) ----
  function skeletons(n) {
    var box = $("wallets"); box.innerHTML = "";
    for (var i = 0; i < n; i++) {
      var d = document.createElement("div"); d.className = "wcard skeleton"; box.appendChild(d);
    }
  }
  function tipoLabel(t) {
    return ({ contanti: "Contanti", carta: "Carte & Wallet", conto: "Conto", investimento: "Investimenti" }[t] || "Altro");
  }
  function render(stato) {
    var box = $("wallets"); box.innerHTML = "";
    (stato.wallets || []).filter(function (w) { return !w.archiviato && !w.deleted; })
      .forEach(function (w) {
        var c = document.createElement("div");
        c.className = "wcard";
        if (w.colore) { c.setAttribute("data-accent", "1"); c.style.setProperty("--wc", w.colore); }
        c.innerHTML =
          '<div><div class="wname">' + escapeHtml(w.nome) + "</div>" +
          '<div class="wtype">' + tipoLabel(w.tipo) + "</div></div>" +
          '<div class="wval num">' + eur(w.saldo) + "</div>";
        box.appendChild(c);
      });
    $("totale").textContent = eur(stato.totale || 0);
    if (stato.mese) {
      $("mese").textContent = "Questo mese: +" + eur(stato.mese.entrate) + " · −" + eur(stato.mese.uscite);
    }
    $("empty").hidden = true;
    $("sync-info").textContent = "Dati dal PC (locale) · " + new Date().toLocaleTimeString(lang, { hour: "2-digit", minute: "2-digit" });
  }
  function statoVuoto() {
    $("wallets").innerHTML = "";
    $("empty").hidden = false;
    $("totale").textContent = "—";
    $("mese").textContent = "";
  }
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (m) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[m];
    });
  }

  skeletons(3);
  // base API: vuota = stessa origine (/api/...). In futuro il telefono potrà
  // puntarla all'indirizzo del PC in LAN salvando "mm_api_base" in localStorage.
  var API_BASE = "";
  try { API_BASE = localStorage.getItem("mm_api_base") || ""; } catch (e) {}
  var ctrl = new AbortController();
  var timer = setTimeout(function () { ctrl.abort(); }, 2500);
  fetch(API_BASE + "/api/finanze/stato", { signal: ctrl.signal, headers: { "Accept": "application/json" } })
    .then(function (r) {
      clearTimeout(timer);
      var ct = r.headers.get("content-type") || "";
      if (!r.ok || ct.indexOf("application/json") < 0) throw new Error("no-api");
      return r.json();
    })
    .then(render)
    .catch(function () { statoVuoto(); });
})();
