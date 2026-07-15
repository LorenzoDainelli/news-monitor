/* MyMoney PWA — app (v2 Fase 4). Finanze OFFLINE sul telefono + sync bidirezionale.
   - i dati vivono in IndexedDB (db.js); il calcolo è in finance.js;
   - all'avvio, se c'è rete, fullSync (push ops locali + pull ops PC) via sync.js;
   - puoi aggiungere movimenti dal telefono: restano in locale con uid/rev/updated_at,
     e vengono registrati nel diario per la sincronizzazione;
   - bottone 🔄 Sincronizza per sync manuale. */
(function () {
  "use strict";
  var lang = "it";
  var $ = function (id) { return document.getElementById(id); };
  var eur = function (n) { return "€ " + Number(n).toLocaleString(lang, { minimumFractionDigits: 2, maximumFractionDigits: 2 }); };
  var nowLocalInput = function () {
    var d = new Date(), p = function (n) { return String(n).padStart(2, "0"); };
    return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()) + "T" + p(d.getHours()) + ":" + p(d.getMinutes());
  };
  var parseImporto = function (s) { return parseFloat(String(s || "").replace(/\./g, "").replace(",", ".")) || 0; };

  // ---------- service worker ----------
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () { navigator.serviceWorker.register("sw.js").catch(function () {}); });
  }

  // ---------- rete ----------
  function segnalaRete() {
    var on = navigator.onLine;
    $("net").textContent = on ? "online" : "offline";
    $("dot").className = "dot " + (on ? "online" : "offline");
  }
  window.addEventListener("online", function () { segnalaRete(); doSync().then(render); });
  window.addEventListener("offline", segnalaRete);

  // ---------- installazione (iOS) ----------
  var isStandalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
  if (/iphone|ipad|ipod/i.test(navigator.userAgent) && !isStandalone) $("install-hint").hidden = false;

  // ---------- API base ----------
  function apiBase() { try { return localStorage.getItem("mm_api_base") || ""; } catch (e) { return ""; } }

  // ---------- sync bidirezionale (Fase 4) ----------
  var _syncing = false;

  function doSync() {
    if (_syncing || !navigator.onLine) return Promise.resolve(false);
    _syncing = true;
    var btn = $("sync-btn");
    if (btn) { btn.disabled = true; btn.textContent = "⏳ Sync…"; }
    return SYNC.fullSync(apiBase()).then(function (result) {
      _syncing = false;
      if (btn) { btn.disabled = false; btn.textContent = "🔄 Sincronizza"; }
      return result.ok;
    }).catch(function () {
      _syncing = false;
      if (btn) { btn.disabled = false; btn.textContent = "🔄 Sincronizza"; }
      return false;
    });
  }

  // ---------- render ----------
  function tipoLabel(t) { return ({ contanti: "Contanti", carta: "Carte & Wallet", conto: "Conto", investimento: "Investimenti" }[t] || "Altro"); }
  function escapeHtml(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (m) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[m]; }); }

  var _wallets = [], _cats = [], _movs = [];

  function render() {
    return Promise.all([DB.getAll("wallets"), DB.getAll("categorie"), DB.getAll("movimenti"), DB.getMeta("last_sync")])
      .then(function (r) {
        _wallets = (r[0] || []).filter(function (w) { return !w.deleted; });
        _cats = (r[1] || []).filter(function (c) { return !c.deleted; });
        _movs = (r[2] || []).filter(function (m) { return !m.deleted; });
        var lastSync = r[3];

        // Senza portafogli il telefono non ha ancora dati (arrivano con la sync):
        // niente form (inutilizzabile senza portafogli), stato "vuoto" in evidenza.
        var vuoto = !_wallets.length;
        $("empty").hidden = !vuoto;
        $("add").hidden = vuoto;
        if (vuoto) { $("add-form").hidden = true; $("lista-sec").hidden = true; $("wallets").innerHTML = ""; }

        var saldoMap = FIN.saldi(_wallets, _movs);
        var tot = FIN.totale(_wallets, saldoMap);
        var now = new Date();
        var riep = FIN.riepilogoMese(_movs, now.getFullYear(), now.getMonth() + 1);
        $("totale").textContent = vuoto ? "—" : eur(tot);
        $("mese").textContent = vuoto ? "In attesa della sincronizzazione" : ("Questo mese: +" + eur(riep.entrate) + " · −" + eur(riep.uscite));

        // card portafogli
        var box = $("wallets"); box.innerHTML = "";
        _wallets.slice().sort(function (a, b) {
          var ai = a.tipo === "investimento", bi = b.tipo === "investimento";
          if (ai !== bi) return ai ? 1 : -1;
          return (saldoMap[b.uid] || 0) - (saldoMap[a.uid] || 0);
        }).forEach(function (w) {
          var c = document.createElement("div"); c.className = "wcard";
          if (w.colore) { c.setAttribute("data-accent", "1"); c.style.setProperty("--wc", w.colore); }
          c.innerHTML = '<div><div class="wname">' + escapeHtml(w.nome) + '</div><div class="wtype">' + tipoLabel(w.tipo) + '</div></div>' +
            '<div class="wval num">' + eur(saldoMap[w.uid] || 0) + '</div>';
          box.appendChild(c);
        });

        // lista movimenti (ultimi 40, per data desc)
        renderLista(saldoMap);
        popolaForm();

        // info sync
        $("sync-info").textContent = lastSync
          ? ("Ultima sync: " + new Date(lastSync).toLocaleString(lang, { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }))
          : (navigator.onLine ? "Non ancora sincronizzato" : "Offline");
      });
  }

  function walletNome(uid) { var w = _wallets.find(function (x) { return x.uid === uid; }); return w ? w.nome : "—"; }
  function catNome(uid) { var c = _cats.find(function (x) { return x.uid === uid; }); return c ? c.nome : null; }

  function renderLista() {
    var lista = $("lista");
    var movs = _movs.slice().sort(function (a, b) { return new Date(b.data) - new Date(a.data); }).slice(0, 40);
    if (!movs.length) { $("lista-sec").hidden = true; return; }
    $("lista-sec").hidden = false;
    lista.innerHTML = "";
    movs.forEach(function (m) {
      var row = document.createElement("div"); row.className = "mrow";
      var d = new Date(m.data);
      var data = d.toLocaleDateString(lang, { day: "2-digit", month: "2-digit" });
      var imp, cls, sub;
      if (m.tipo === "giro") {
        var gd = FIN.giroDisplay(m); cls = "muted";
        imp = (gd > 0 ? "+" : gd < 0 ? "−" : "") + eur(Math.abs(gd));
        sub = "Giro" + (m.controparte ? " · " + escapeHtml(m.controparte) : "") + " · " + walletNome(m.wallet_uid);
      } else if (m.tipo === "entrata") { cls = "pos"; imp = "+" + eur(m.importo); sub = (catNome(m.categoria_uid) || "Entrata") + " · " + walletNome(m.wallet_uid); }
      else if (m.tipo === "uscita") { cls = "neg"; imp = "−" + eur(m.importo); sub = (catNome(m.categoria_uid) || "Uscita") + " · " + walletNome(m.wallet_uid); }
      else { cls = ""; imp = eur(m.importo); sub = walletNome(m.wallet_uid) + " → " + walletNome(m.wallet_to_uid); }
      row.innerHTML =
        '<div class="mmain"><div class="mdesc">' + (escapeHtml(m.descrizione) || sub) + '</div>' +
        '<div class="msub">' + data + " · " + escapeHtml(sub) + '</div></div>' +
        '<div class="mval num ' + cls + '">' + imp + '</div>';
      lista.appendChild(row);
    });
  }

  // ---------- form aggiungi movimento ----------
  function popolaForm() {
    ["af-wallet", "af-wallet-to"].forEach(function (id) {
      var sel = $(id), cur = sel.value; sel.innerHTML = "";
      _wallets.forEach(function (w) { var o = document.createElement("option"); o.value = w.uid; o.textContent = w.nome; sel.appendChild(o); });
      if (cur) sel.value = cur;
    });
    var dl = $("af-cats"); dl.innerHTML = "";
    _cats.forEach(function (c) { var o = document.createElement("option"); o.value = c.nome; dl.appendChild(o); });
  }

  function toggleForm(show) {
    var f = $("add-form");
    var open = show == null ? f.hidden : show;
    f.hidden = !open;
    if (open) { if (!$("af-data").value) $("af-data").value = nowLocalInput(); $("af-tipo").dispatchEvent(new Event("change")); }
  }

  $("add").addEventListener("click", function () { toggleForm(true); });
  $("af-cancel").addEventListener("click", function () { toggleForm(false); });
  $("af-tipo").addEventListener("change", function () {
    var t = $("af-tipo").value;
    $("af-wallet-to-lab").hidden = t !== "trasferimento";
    $("af-cat-row").style.display = t === "trasferimento" ? "none" : "";
    $("af-wallet-lab").firstChild.textContent = t === "trasferimento" ? "Da portafoglio" : "Portafoglio";
  });

  function trovaOCreaCategoria(nome, kind) {
    nome = (nome || "").trim();
    if (!nome) return Promise.resolve(null);
    var ex = _cats.find(function (c) { return c.nome.toLowerCase() === nome.toLowerCase(); });
    if (ex) return Promise.resolve(ex.uid);
    var c = { uid: nuovoUid(), nome: nome, kind: kind || "", archiviato: false, deleted: false, rev: 1, updated_at: new Date().toISOString(), _local: true };
    return DB.put("categorie", c).then(function () {
      _cats.push(c);
      // Registra nel diario per la sync
      return SYNC.getDeviceId().then(function (did) {
        return SYNC.recordOp("category", "upsert", c, did);
      }).then(function () { return c.uid; });
    });
  }

  $("add-form").addEventListener("submit", function (e) {
    e.preventDefault();
    var t = $("af-tipo").value;
    var importo = parseImporto($("add-form").importo.value);
    if (importo <= 0) return;
    var wallet_uid = $("af-wallet").value;
    var wallet_to_uid = t === "trasferimento" ? $("af-wallet-to").value : null;
    if (t === "trasferimento" && wallet_to_uid === wallet_uid) { alert("Scegli due portafogli diversi."); return; }
    var data = $("af-data").value || nowLocalInput();
    var descrizione = $("add-form").descrizione.value || "";
    var catNomeIn = t === "trasferimento" ? "" : $("add-form").categoria.value;

    trovaOCreaCategoria(catNomeIn, t).then(function (catUid) {
      var m = {
        uid: nuovoUid(), tipo: t, data: data, importo: Math.abs(importo),
        wallet_uid: wallet_uid, wallet_to_uid: wallet_to_uid,
        categoria_uid: catUid, descrizione: descrizione.trim(),
        giro_id: "", giro_aperta: false, importo_ricevuto: null, data_ricevuto: null, controparte: "",
        rev: 1, updated_at: new Date().toISOString(), deleted: false, _local: true
      };
      return DB.put("movimenti", m).then(function () {
        // Registra nel diario per la sync
        return SYNC.getDeviceId().then(function (did) {
          return SYNC.recordOp("transaction", "upsert", m, did);
        });
      });
    }).then(function () {
      $("add-form").reset(); $("af-data").value = nowLocalInput();
      toggleForm(false);
      return render();
    });
  });

  // ---------- bottone sync ----------
  $("sync-btn").addEventListener("click", function () {
    doSync().then(function (ok) {
      render();
    });
  });

  // ---------- Google Drive (Fase 5) ----------
  // drive.js potrebbe non essere ancora arrivato (deploy/cache a metà) o il
  // guscio in cache potrebbe essere una versione senza i bottoni Drive: in quel
  // caso l'app deve funzionare LO STESSO, solo senza Drive. Mai bloccare l'avvio.
  var HAS_DRIVE = (typeof DRIVE !== "undefined") && !!$("drive-btn");

  function doDriveSync() {
    if (!HAS_DRIVE) return Promise.resolve();
    var btn = $("drive-btn");
    if (btn) { btn.disabled = true; btn.textContent = "⏳ Drive…"; }
    return DRIVE.driveSync().then(function (r) {
      if (btn) { btn.disabled = false; btn.textContent = "☁️ Drive"; }
      if (r.ok) return render();   // render mostra "Ultima sync: …"
      $("sync-info").textContent = r.reason === "token"
        ? "Drive: tocca di nuovo ☁️ per accedere"
        : "Drive: errore (" + r.reason + ")";
    });
  }

  if (HAS_DRIVE) {
    $("drive-btn").addEventListener("click", function () {
      DRIVE.getClientId().then(function (cid) {
        if (!cid) { if ($("drive-setup")) $("drive-setup").hidden = false; return; }
        DRIVE.getToken().then(function (tok) {
          if (!tok) { DRIVE.connect(); return; }   // redirect a Google e ritorno
          doDriveSync();
        });
      });
    });
    if ($("drive-cid-save")) {
      $("drive-cid-save").addEventListener("click", function () {
        var v = $("drive-cid").value.trim();
        if (!v) return;
        DRIVE.setClientId(v).then(function () {
          $("drive-setup").hidden = true;
          DRIVE.connect();
        });
      });
    }
    if ($("drive-cid-cancel")) {
      $("drive-cid-cancel").addEventListener("click", function () { $("drive-setup").hidden = true; });
    }
  }

  // ---------- export/import manuale ----------
  if ($("export-btn")) {
    $("export-btn").addEventListener("click", function () {
      SYNC.exportBundle().then(function (bundle) {
        var blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
        var a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "mymoney-export.json";
        a.click();
        URL.revokeObjectURL(a.href);
      });
    });
  }
  if ($("import-btn")) {
    $("import-btn").addEventListener("click", function () {
      var input = document.createElement("input");
      input.type = "file"; input.accept = ".json";
      input.onchange = function () {
        var f = input.files[0]; if (!f) return;
        var reader = new FileReader();
        reader.onload = function () {
          try {
            var data = JSON.parse(reader.result);
            SYNC.importBundle(data).then(function (result) {
              alert("Importati: " + result.applied + " record.");
              render();
            });
          } catch (e) { alert("File non valido."); }
        };
        reader.readAsText(f);
      };
      input.click();
    });
  }

  // ---------- boot ----------
  segnalaRete();
  // Se stiamo TORNANDO dal consenso Google (token nel fragment), salvalo e
  // parti subito con la sync via Drive; altrimenti la solita sync HTTP (LAN).
  var driveBoot = HAS_DRIVE ? DRIVE.handleRedirect() : Promise.resolve(false);
  driveBoot.then(function (daGoogle) {
    return render().then(function () {
      if (daGoogle) return doDriveSync();
      return doSync().then(function (ok) { if (ok) return render(); });
    });
  }).catch(function () {
    // Qualunque cosa vada storta nell'avvio, l'app deve almeno mostrarsi.
    try { render(); } catch (e) {}
  });
})();
