/* MyMoney PWA — app (v3, redesign "app"). Finanze OFFLINE sul telefono + sync.
   - i dati vivono in IndexedDB (db.js); il calcolo è in finance.js;
   - struttura a schede (Home/Movimenti/Conti/Sync) con barra in basso e FAB;
   - il form Aggiungi vive in un pannello che sale dal fondo (sheet);
   - all'avvio, se c'è rete, sync (via Drive al ritorno da Google, altrimenti LAN);
   - il motore dati/sync (db.js/finance.js/sync.js/drive.js) è invariato. */
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
  function escapeHtml(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (m) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[m]; }); }
  function tipoLabel(t) { return ({ contanti: "Contanti", carta: "Carte & Wallet", conto: "Conto", investimento: "Investimenti" }[t] || "Altro"); }

  // ---------- service worker ----------
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () { navigator.serviceWorker.register("sw.js").catch(function () {}); });
  }

  // ---------- rete ----------
  function segnalaRete() {
    var on = navigator.onLine;
    if ($("net")) $("net").textContent = on ? "online" : "offline";
    if ($("dot")) $("dot").className = "dot " + (on ? "online" : "offline");
  }
  window.addEventListener("online", function () { segnalaRete(); doSync().then(render); });
  window.addEventListener("offline", segnalaRete);

  // ---------- installazione (iOS) ----------
  var isStandalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
  if (/iphone|ipad|ipod/i.test(navigator.userAgent) && !isStandalone && $("install-hint")) $("install-hint").hidden = false;

  // ---------- API base (rete locale) ----------
  function apiBase() { try { return localStorage.getItem("mm_api_base") || ""; } catch (e) { return ""; } }

  // ---------- navigazione a schede ----------
  var TABS = ["home", "movimenti", "conti", "sync"];
  function setTab(name) {
    TABS.forEach(function (n) { var v = $("view-" + n); if (v) v.hidden = n !== name; });
    document.querySelectorAll(".tab").forEach(function (t) { t.classList.toggle("on", t.getAttribute("data-tab") === name); });
    window.scrollTo(0, 0);
  }
  document.querySelectorAll(".tab").forEach(function (t) {
    t.addEventListener("click", function () { setTab(t.getAttribute("data-tab")); });
  });
  document.querySelectorAll("[data-goto]").forEach(function (b) {
    b.addEventListener("click", function () { setTab(b.getAttribute("data-goto")); });
  });

  // ---------- sync rete locale (Fase 4) ----------
  var _syncing = false;
  function doSync() {
    if (_syncing || !navigator.onLine) return Promise.resolve(false);
    _syncing = true;
    var btn = $("sync-btn"), orig = btn ? btn.textContent : "";
    if (btn) { btn.disabled = true; btn.textContent = "⏳ Sync…"; }
    return SYNC.fullSync(apiBase()).then(function (result) {
      _syncing = false; if (btn) { btn.disabled = false; btn.textContent = orig; }
      return result.ok;
    }).catch(function () {
      _syncing = false; if (btn) { btn.disabled = false; btn.textContent = orig; }
      return false;
    });
  }

  // ---------- dati in memoria ----------
  var _wallets = [], _cats = [], _movs = [];
  function walletNome(uid) { var w = _wallets.find(function (x) { return x.uid === uid; }); return w ? w.nome : "—"; }
  function catNome(uid) { var c = _cats.find(function (x) { return x.uid === uid; }); return c ? c.nome : null; }

  function dateLabel(iso) {
    var d = new Date(iso); if (isNaN(d)) return "";
    var now = new Date();
    var a = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    var b = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    var diff = Math.round((b - a) / 86400000);
    if (diff === 0) return "oggi";
    if (diff === 1) return "ieri";
    return d.toLocaleDateString(lang, { day: "2-digit", month: "2-digit" });
  }

  // riga movimento -> {main, sub, val, cls}
  function movToView(m) {
    var cls, val, sub;
    if (m.tipo === "giro") {
      var gd = FIN.giroDisplay(m); cls = "muted";
      val = (gd > 0 ? "+" : gd < 0 ? "−" : "") + eur(Math.abs(gd));
      sub = "Giro" + (m.controparte ? " · " + m.controparte : "") + " · " + walletNome(m.wallet_uid);
    } else if (m.tipo === "entrata") {
      cls = "pos"; val = "+" + eur(m.importo); sub = (catNome(m.categoria_uid) || "Entrata") + " · " + walletNome(m.wallet_uid);
    } else if (m.tipo === "uscita") {
      cls = "neg"; val = "−" + eur(m.importo); sub = (catNome(m.categoria_uid) || "Uscita") + " · " + walletNome(m.wallet_uid);
    } else {
      cls = ""; val = eur(m.importo); sub = walletNome(m.wallet_uid) + " → " + walletNome(m.wallet_to_uid);
    }
    return { main: m.descrizione ? m.descrizione : sub, sub: sub, val: val, cls: cls };
  }

  function renderConti(box, wallets, saldoMap, compact) {
    if (!box) return;
    box.innerHTML = "";
    wallets.forEach(function (w) {
      var val = saldoMap[w.uid] || 0, neg = val < 0 ? " neg" : "";
      var c = document.createElement("div");
      if (w.colore) c.style.setProperty("--wc", w.colore);
      if (compact) {
        c.className = "cchip";
        c.innerHTML = '<div class="n">' + escapeHtml(w.nome) + '</div>' +
          '<div class="v num' + neg + '">' + eur(val) + '</div>';
      } else {
        c.className = "wcard";
        c.innerHTML = '<div class="wmain"><div class="wname">' + escapeHtml(w.nome) + '</div>' +
          '<div class="wtype">' + tipoLabel(w.tipo) + '</div></div>' +
          '<div class="wval num' + neg + '">' + eur(val) + '</div>';
      }
      box.appendChild(c);
    });
  }

  function renderMovimenti(box, movs, dayHeaders) {
    if (!box) return;
    box.innerHTML = "";
    var lastDay = null;
    movs.forEach(function (m) {
      if (dayHeaders) {
        var dl = dateLabel(m.data);
        if (dl !== lastDay) { var h = document.createElement("div"); h.className = "day-h"; h.textContent = dl; box.appendChild(h); lastDay = dl; }
      }
      var v = movToView(m);
      var row = document.createElement("div"); row.className = "mrow"; row.setAttribute("data-uid", m.uid);
      var subTxt = dayHeaders ? v.sub : (dateLabel(m.data) + " · " + v.sub);
      row.innerHTML = '<div class="mmain"><div class="mdesc">' + escapeHtml(v.main) + '</div>' +
        '<div class="msub">' + escapeHtml(subTxt) + '</div></div>' +
        '<div class="mval num ' + v.cls + '">' + v.val + '</div>' +
        '<svg class="ic mchev" aria-hidden="true"><use href="#ic-chevron"/></svg>';
      box.appendChild(row);
    });
  }

  function render() {
    return Promise.all([DB.getAll("wallets"), DB.getAll("categorie"), DB.getAll("movimenti"), DB.getMeta("last_sync"), DB.getMeta("needs_update")])
      .then(function (r) {
        _wallets = (r[0] || []).filter(function (w) { return !w.deleted; });
        _cats = (r[1] || []).filter(function (c) { return !c.deleted; });
        _movs = (r[2] || []).filter(function (m) { return !m.deleted; });
        var lastSync = r[3], needsUpdate = !!r[4];

        var banner = $("drive-needs-update");
        if (banner) banner.classList.toggle("hide", !needsUpdate);

        var vuoto = !_wallets.length;
        $("empty").hidden = !vuoto;
        $("home-full").hidden = vuoto;
        if ($("fab")) $("fab").style.visibility = vuoto ? "hidden" : "";

        var saldoMap = FIN.saldi(_wallets, _movs);
        var tot = FIN.totale(_wallets, saldoMap);
        var now = new Date();
        var riep = FIN.riepilogoMese(_movs, now.getFullYear(), now.getMonth() + 1);
        $("totale").textContent = vuoto ? "—" : eur(tot);
        $("mese").textContent = vuoto ? "In attesa della sincronizzazione"
          : ("Questo mese +" + eur(riep.entrate) + " · −" + eur(riep.uscite));

        // conti: investimenti in fondo, poi per |saldo| decrescente
        var ordinati = _wallets.slice().sort(function (a, b) {
          var ai = a.tipo === "investimento", bi = b.tipo === "investimento";
          if (ai !== bi) return ai ? 1 : -1;
          return Math.abs(saldoMap[b.uid] || 0) - Math.abs(saldoMap[a.uid] || 0);
        });
        renderConti($("home-conti"), ordinati.slice(0, 2), saldoMap, true);
        renderConti($("lista-conti"), ordinati, saldoMap, false);
        $("conti-vuoto").hidden = !!_wallets.length;

        var movOrd = _movs.slice().sort(function (a, b) { return new Date(b.data) - new Date(a.data); });
        renderMovimenti($("home-movimenti"), movOrd.slice(0, 5), false);
        renderMovimenti($("lista-movimenti"), movOrd.slice(0, 200), true);
        $("movimenti-vuoto").hidden = !!_movs.length;

        popolaForm();
        renderSyncInfo(lastSync, needsUpdate);
      });
  }

  function renderSyncInfo(lastSync, needsUpdate) {
    var stale = $("stale");
    if (stale) {
      if (!lastSync) { stale.hidden = false; stale.textContent = "Non hai ancora sincronizzato questo telefono."; }
      else {
        var days = (new Date() - new Date(lastSync)) / 86400000;
        if (days > 7) { stale.hidden = false; stale.textContent = "Ultima sincronizzazione oltre una settimana fa — tocca ☁️ Drive per aggiornare."; }
        else stale.hidden = true;
      }
    }
    if ($("sync-info")) $("sync-info").textContent = lastSync
      ? ("Ultima sync: " + new Date(lastSync).toLocaleString(lang, { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }))
      : (navigator.onLine ? "Non ancora sincronizzato" : "Offline");
    if ($("sync-btn")) $("sync-btn").classList.toggle("stale", needsUpdate);
    if ($("drive-btn")) $("drive-btn").classList.toggle("stale", needsUpdate);
  }

  // ---------- pannelli (sheet): Aggiungi / Modifica / Dettaglio ----------
  var _editUid = null, _detailUid = null;
  function showSheet(id) {
    $("backdrop").classList.add("show");
    $(id).classList.add("show");
    document.body.classList.add("locked");
  }
  function hideSheets() {
    $("backdrop").classList.remove("show");
    document.querySelectorAll(".sheet").forEach(function (s) { s.classList.remove("show"); });
    document.body.classList.remove("locked");
  }
  if ($("backdrop")) $("backdrop").addEventListener("click", hideSheets);

  // --- Aggiungi / Modifica ---
  function openSheet(mov) {
    if (!_wallets.length) return;   // senza conti non si può aggiungere
    _editUid = mov ? mov.uid : null;
    if ($("add-title")) $("add-title").textContent = mov ? "Modifica movimento" : "Nuovo movimento";
    if (mov) {
      prefillForm(mov);
    } else {
      $("add-form").reset(); setTipo("uscita"); $("af-data").value = nowLocalInput();
    }
    showSheet("add-sheet");
  }
  function prefillForm(m) {
    popolaForm();
    setTipo(m.tipo);
    var f = $("add-form");
    f.importo.value = (m.importo != null) ? Number(m.importo).toLocaleString("it-IT", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "";
    $("af-wallet").value = m.wallet_uid || "";
    if (m.tipo === "trasferimento") $("af-wallet-to").value = m.wallet_to_uid || "";
    f.categoria.value = (m.tipo === "trasferimento") ? "" : (catNome(m.categoria_uid) || "");
    $("af-data").value = String(m.data || nowLocalInput()).slice(0, 16);
    f.descrizione.value = m.descrizione || "";
  }
  if ($("fab")) $("fab").addEventListener("click", function () { openSheet(); });
  if ($("af-cancel")) $("af-cancel").addEventListener("click", hideSheets);

  // --- Dettaglio movimento (tocco su una riga) ---
  function tipoNome(t) { return ({ uscita: "Uscita", entrata: "Entrata", trasferimento: "Trasferimento", giro: "Partita di giro" }[t] || t); }
  function dataEstesa(iso) { var d = new Date(iso); return isNaN(d) ? String(iso || "") : d.toLocaleString(lang, { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }); }
  function drow(label, val) { return '<div class="drow"><span class="dl">' + label + '</span><span class="dv">' + escapeHtml(val) + '</span></div>'; }
  function openDetail(m) {
    _detailUid = m.uid;
    var v = movToView(m), html = "";
    html += drow("Tipo", tipoNome(m.tipo));
    html += '<div class="drow"><span class="dl">Importo</span><span class="dv ' + v.cls + '">' + v.val + '</span></div>';
    if (m.tipo === "trasferimento") { html += drow("Da", walletNome(m.wallet_uid)); html += drow("A", walletNome(m.wallet_to_uid)); }
    else { html += drow("Portafoglio", walletNome(m.wallet_uid)); }
    if (m.tipo !== "trasferimento" && m.categoria_uid) html += drow("Categoria", catNome(m.categoria_uid) || "—");
    if (m.tipo === "giro" && m.controparte) html += drow("Controparte", m.controparte);
    html += drow("Data", dataEstesa(m.data));
    if (m.descrizione) html += drow("Descrizione", m.descrizione);
    $("detail-body").innerHTML = html;
    $("detail-title").textContent = m.descrizione ? m.descrizione : v.sub;
    $("detail-edit").style.display = (m.tipo === "giro") ? "none" : "";
    showSheet("detail-sheet");
  }
  document.addEventListener("click", function (e) {
    var row = e.target.closest ? e.target.closest(".mrow") : null;
    if (!row) return;
    var m = _movs.find(function (x) { return x.uid === row.getAttribute("data-uid"); });
    if (m) openDetail(m);
  });
  if ($("detail-close")) $("detail-close").addEventListener("click", hideSheets);
  if ($("detail-edit")) $("detail-edit").addEventListener("click", function () {
    var m = _movs.find(function (x) { return x.uid === _detailUid; });
    hideSheets(); if (m) openSheet(m);
  });
  if ($("detail-del")) $("detail-del").addEventListener("click", function () {
    var m = _movs.find(function (x) { return x.uid === _detailUid; });
    if (!m) return;
    if (!confirm("Eliminare questo movimento? Verrà tolto anche dagli altri dispositivi alla prossima sincronizzazione.")) return;
    var del = Object.assign({}, m, { deleted: true, rev: (m.rev || 1) + 1, updated_at: new Date().toISOString(), _local: true });
    DB.put("movimenti", del)
      .then(function () { return SYNC.getDeviceId().then(function (did) { return SYNC.recordOp("transaction", "delete", del, did); }); })
      .then(function () { hideSheets(); return render(); });
  });

  function setTipo(t) {
    var isT = t === "trasferimento";
    $("af-tipo").value = t;
    document.querySelectorAll("#type-picker .ty").forEach(function (b) {
      b.classList.toggle("on", b.getAttribute("data-tipo") === t);
    });
    $("af-wallet-to-lab").hidden = !isT;
    $("af-cat-row").style.display = isT ? "none" : "";
    // senza "A portafoglio" il Portafoglio prende tutta la larghezza (niente mezzo vuoto)
    $("af-wallet-lab").classList.toggle("af-full", !isT);
    $("af-wallet-lab").firstChild.textContent = isT ? "Da portafoglio" : "Portafoglio";
  }
  document.querySelectorAll("#type-picker .ty").forEach(function (b) {
    b.addEventListener("click", function () { setTipo(b.getAttribute("data-tipo")); });
  });
  setTipo("uscita");   // stato iniziale coerente (Portafoglio a tutta larghezza)

  function popolaForm() {
    ["af-wallet", "af-wallet-to"].forEach(function (id) {
      var sel = $(id), cur = sel.value; sel.innerHTML = "";
      _wallets.forEach(function (w) { var o = document.createElement("option"); o.value = w.uid; o.textContent = w.nome; sel.appendChild(o); });
      if (cur) sel.value = cur;
    });
    var dl = $("af-cats"); dl.innerHTML = "";
    _cats.forEach(function (c) { var o = document.createElement("option"); o.value = c.nome; dl.appendChild(o); });
  }

  function trovaOCreaCategoria(nome, kind) {
    nome = (nome || "").trim();
    if (!nome) return Promise.resolve(null);
    var ex = _cats.find(function (c) { return c.nome.toLowerCase() === nome.toLowerCase(); });
    if (ex) return Promise.resolve(ex.uid);
    var c = { uid: nuovoUid(), nome: nome, kind: kind || "", archiviato: false, deleted: false, rev: 1, updated_at: new Date().toISOString(), _local: true };
    return DB.put("categorie", c).then(function () {
      _cats.push(c);
      return SYNC.getDeviceId().then(function (did) { return SYNC.recordOp("category", "upsert", c, did); }).then(function () { return c.uid; });
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
      var editing = _editUid ? _movs.find(function (x) { return x.uid === _editUid; }) : null;
      var m;
      if (editing) {
        // Modifica: stesso uid, rev+1 e updated_at nuovo così la modifica vince
        // (LWW). I campi del giro non toccati dal form vengono conservati.
        m = Object.assign({}, editing, {
          tipo: t, data: data, importo: Math.abs(importo),
          wallet_uid: wallet_uid, wallet_to_uid: wallet_to_uid,
          categoria_uid: catUid, descrizione: descrizione.trim(),
          rev: (editing.rev || 1) + 1, updated_at: new Date().toISOString(),
          deleted: false, _local: true
        });
      } else {
        m = {
          uid: nuovoUid(), tipo: t, data: data, importo: Math.abs(importo),
          wallet_uid: wallet_uid, wallet_to_uid: wallet_to_uid,
          categoria_uid: catUid, descrizione: descrizione.trim(),
          giro_id: "", giro_aperta: false, importo_ricevuto: null, data_ricevuto: null, controparte: "",
          rev: 1, updated_at: new Date().toISOString(), deleted: false, _local: true
        };
      }
      return DB.put("movimenti", m).then(function () {
        return SYNC.getDeviceId().then(function (did) { return SYNC.recordOp("transaction", "upsert", m, did); });
      });
    }).then(function () {
      _editUid = null;
      $("add-form").reset(); setTipo("uscita"); $("af-data").value = nowLocalInput();
      hideSheets();
      return render();
    });
  });

  // ---------- Google Drive (Fase 5) ----------
  var HAS_DRIVE = (typeof DRIVE !== "undefined") && !!$("drive-btn");
  function doDriveSync() {
    if (!HAS_DRIVE) return Promise.resolve();
    var btn = $("drive-btn");
    if (btn) { btn.disabled = true; btn.textContent = "⏳ Drive…"; }
    return DRIVE.driveSync().then(function (r) {
      if (btn) { btn.disabled = false; btn.textContent = "☁️ Drive"; }
      if (r.ok) return render();
      if ($("sync-info")) $("sync-info").textContent = r.reason === "token"
        ? "Drive: tocca di nuovo ☁️ per accedere"
        : (r.reason === "quota" ? "Drive: spazio esaurito" : "Drive: errore (" + r.reason + ")");
    });
  }
  if (HAS_DRIVE) {
    $("drive-btn").addEventListener("click", function () {
      DRIVE.getClientId().then(function (cid) {
        if (!cid) { if ($("drive-setup")) $("drive-setup").hidden = false; return; }
        DRIVE.getToken().then(function (tok) {
          if (!tok) { DRIVE.connect(); return; }
          doDriveSync();
        });
      });
    });
    if ($("drive-cid-save")) {
      $("drive-cid-save").addEventListener("click", function () {
        var v = $("drive-cid").value.trim(); if (!v) return;
        DRIVE.setClientId(v).then(function () { $("drive-setup").hidden = true; DRIVE.connect(); });
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
        a.href = URL.createObjectURL(blob); a.download = "mymoney-export.json"; a.click();
        URL.revokeObjectURL(a.href);
      });
    });
  }
  if ($("import-btn")) {
    $("import-btn").addEventListener("click", function () {
      var input = document.createElement("input"); input.type = "file"; input.accept = ".json";
      input.onchange = function () {
        var f = input.files[0]; if (!f) return;
        var reader = new FileReader();
        reader.onload = function () {
          try {
            var data = JSON.parse(reader.result);
            SYNC.importBundle(data).then(function (result) { alert("Importati: " + result.applied + " record."); render(); });
          } catch (e) { alert("File non valido."); }
        };
        reader.readAsText(f);
      };
      input.click();
    });
  }

  // ---------- boot ----------
  segnalaRete();
  var driveBoot = HAS_DRIVE ? DRIVE.handleRedirect() : Promise.resolve(false);
  driveBoot.then(function (daGoogle) {
    if (daGoogle) setTab("sync");   // torni da Google: mostro l'esito nella scheda Sync
    return render().then(function () {
      if (daGoogle) return doDriveSync();
      return doSync().then(function (ok) { if (ok) return render(); });
    });
  }).catch(function () {
    try { render(); } catch (e) {}
  });
})();
