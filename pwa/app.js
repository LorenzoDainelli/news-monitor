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
  window.addEventListener("online", function () { segnalaRete(); if (typeof MIRROR !== "undefined" && MIRROR) MIRROR.autoOnOpen(); });
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
    // aprendo la scheda Sync ri-controllo la copia a specchio (stato + auto-scarica sicura)
    if (name === "sync" && typeof MIRROR !== "undefined" && MIRROR) MIRROR.autoOnOpen();
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
    // Il vecchio banner "stale" e l'info dell'ultima fusione non servono più: il
    // modello a specchio ha il suo stato (mirror-info + pillola). Resta solo
    // l'evidenza rossa sul pulsante quando l'altro dispositivo usa una versione
    // più recente dell'app.
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
    // chiudi la tastiera (altrimenti su iOS resta su e il layout resta "corto")
    if (document.activeElement && document.activeElement.blur) { try { document.activeElement.blur(); } catch (e) {} }
    $("backdrop").classList.remove("show");
    document.querySelectorAll(".sheet").forEach(function (s) { s.classList.remove("show"); });
    document.body.classList.remove("locked");
  }
  if ($("backdrop")) $("backdrop").addEventListener("click", hideSheets);

  // ---------- tastiera iOS: tieni il pannello SOPRA la tastiera ----------
  /* Su iOS la tastiera copre il pannello che sale dal fondo: sembra "bloccato"
     perché il campo e il pulsante Salva finiscono sotto la tastiera. Con la
     visualViewport misuriamo l'altezza della tastiera (--kb) e l'area visibile
     (--vvh): il CSS alza il pannello e ne riduce l'altezza; qui portiamo anche
     in vista il campo che stai scrivendo. */
  (function () {
    var vv = window.visualViewport; if (!vv) return;
    function onVV() {
      var kb = Math.max(0, Math.round(window.innerHeight - vv.height - vv.offsetTop));
      var root = document.documentElement;
      root.style.setProperty("--kb", kb + "px");
      root.style.setProperty("--vvh", Math.round(vv.height) + "px");
      document.body.classList.toggle("kbd", kb > 60);   // soglia: ignora micro-variazioni della barra
    }
    vv.addEventListener("resize", onVV);
    vv.addEventListener("scroll", onVV);
  })();
  document.addEventListener("focusin", function (e) {
    if (!document.body.classList.contains("locked")) return;
    var el = e.target; if (!el || !el.scrollIntoView) return;
    setTimeout(function () { try { el.scrollIntoView({ block: "center", behavior: "smooth" }); } catch (e2) {} }, 250);
  });

  // --- Aggiungi / Modifica ---
  function openSheet(mov) {
    if (!_wallets.length) return;   // senza conti non si può aggiungere
    _editUid = mov ? mov.uid : null;
    if ($("add-title")) $("add-title").textContent = mov ? "Modifica movimento" : "Nuovo movimento";
    // riparti sempre con la barra AI chiusa e pulita
    if ($("ai-box")) $("ai-box").hidden = true;
    if ($("ai-text")) $("ai-text").value = "";
    if ($("ai-status")) { $("ai-status").hidden = true; $("ai-status").textContent = ""; }
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
    if ($("af-controparte")) $("af-controparte").value = (m.tipo === "giro") ? (m.controparte || "") : "";
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
    var v = movToView(m), isG = m.tipo === "giro", html = "";
    html += drow("Tipo", tipoNome(m.tipo));
    if (isG) html += drow("Stato", m.giro_aperta ? "Aperta · rimborso in arrivo" : "Chiusa · rimborsata");
    html += '<div class="drow"><span class="dl">' + (isG ? "Anticipato" : "Importo") + '</span><span class="dv ' + v.cls + '">' + (isG ? eur(m.importo) : v.val) + '</span></div>';
    if (m.tipo === "trasferimento") { html += drow("Da", walletNome(m.wallet_uid)); html += drow("A", walletNome(m.wallet_to_uid)); }
    else { html += drow(isG ? "Da portafoglio" : "Portafoglio", walletNome(m.wallet_uid)); }
    if (isG && m.controparte) html += drow("Ti rimborsa", m.controparte);
    if (isG && m.importo_ricevuto != null) html += drow("Rientrato", eur(m.importo_ricevuto) + " · " + walletNome(m.wallet_to_uid));
    if (m.tipo !== "trasferimento" && m.categoria_uid) html += drow("Categoria", catNome(m.categoria_uid) || "—");
    html += drow("Data", dataEstesa(m.data));
    if (m.descrizione) html += drow("Descrizione", m.descrizione);
    $("detail-body").innerHTML = html;
    $("detail-title").textContent = m.descrizione ? m.descrizione : v.sub;
    $("detail-edit").style.display = "";
    if ($("detail-rientro")) $("detail-rientro").style.display = (isG && m.giro_aperta) ? "" : "none";
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
      .then(function () { hideSheets(); return render(); })
      .then(function () { return MIRROR.afterLocalChange(); });
  });

  function setTipo(t) {
    var isT = t === "trasferimento", isG = t === "giro";
    $("af-tipo").value = t;
    document.querySelectorAll("#type-picker .ty").forEach(function (b) {
      b.classList.toggle("on", b.getAttribute("data-tipo") === t);
    });
    $("af-wallet-to-lab").hidden = !isT;
    if ($("af-cat-lab")) $("af-cat-lab").hidden = isT;                    // categoria: uscita/entrata/giro (come sul PC), non trasferimento
    if ($("af-controparte-lab")) $("af-controparte-lab").hidden = !isG;   // controparte solo giro
    // senza "A portafoglio" il Portafoglio prende tutta la larghezza (niente mezzo vuoto)
    $("af-wallet-lab").classList.toggle("af-full", !isT);
    $("af-wallet-lab").firstChild.textContent = (isT || isG) ? "Da portafoglio" : "Portafoglio";
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
    var isT = t === "trasferimento", isG = t === "giro";
    var wallet_uid = $("af-wallet").value;
    var wallet_to_uid = isT ? $("af-wallet-to").value : null;
    if (isT && wallet_to_uid === wallet_uid) { alert("Scegli due portafogli diversi."); return; }
    var data = $("af-data").value || nowLocalInput();
    var descrizione = ($("add-form").descrizione.value || "").trim();
    var controparte = (isG && $("af-controparte")) ? ($("af-controparte").value || "").trim() : "";
    var catNomeIn = isT ? "" : $("add-form").categoria.value;   // categoria anche per il giro (come sul PC)

    trovaOCreaCategoria(catNomeIn, t).then(function (catUid) {
      var editing = _editUid ? _movs.find(function (x) { return x.uid === _editUid; }) : null;
      var m;
      if (editing) {
        // Modifica: stesso uid, rev+1 e updated_at nuovo → la modifica vince (LWW).
        // I campi del giro non toccati dal form (es. rientro) vengono conservati.
        m = Object.assign({}, editing, {
          tipo: t, data: data, importo: Math.abs(importo),
          wallet_uid: wallet_uid,
          wallet_to_uid: isT ? wallet_to_uid : (isG ? (editing.wallet_to_uid || wallet_uid) : null),
          categoria_uid: catUid, descrizione: descrizione,
          controparte: isG ? controparte : "",
          rev: (editing.rev || 1) + 1, updated_at: new Date().toISOString(),
          deleted: false, _local: true
        });
      } else if (isG) {
        // Nuovo giro: parte APERTO (rimborso in arrivo); il rientro si registra
        // poi dal Dettaglio con "Registra rientro".
        m = {
          uid: nuovoUid(), tipo: "giro", data: data, importo: Math.abs(importo),
          wallet_uid: wallet_uid, wallet_to_uid: wallet_uid,
          categoria_uid: catUid, descrizione: descrizione,
          giro_id: "", giro_aperta: true, importo_ricevuto: null, data_ricevuto: null, controparte: controparte,
          rev: 1, updated_at: new Date().toISOString(), deleted: false, _local: true
        };
      } else {
        m = {
          uid: nuovoUid(), tipo: t, data: data, importo: Math.abs(importo),
          wallet_uid: wallet_uid, wallet_to_uid: wallet_to_uid,
          categoria_uid: catUid, descrizione: descrizione,
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
    }).then(function () { return MIRROR.afterLocalChange(); });
  });

  // ---------- Registra rientro (chiude un giro aperto) ----------
  var _rientroUid = null;
  function openRientro(m) {
    _rientroUid = m.uid;
    if ($("rientro-info")) $("rientro-info").textContent = "Da " + (m.controparte || "chi ti rimborsa") + " · anticipato " + eur(m.importo);
    var sel = $("ri-wallet");
    if (sel) {
      sel.innerHTML = "";
      _wallets.forEach(function (w) { var o = document.createElement("option"); o.value = w.uid; o.textContent = w.nome; sel.appendChild(o); });
      sel.value = m.wallet_uid || (_wallets[0] && _wallets[0].uid) || "";
    }
    if ($("ri-importo")) $("ri-importo").value = Number(m.importo).toLocaleString("it-IT", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if ($("ri-data")) $("ri-data").value = nowLocalInput();
    hideSheets(); showSheet("rientro-sheet");
  }
  if ($("detail-rientro")) $("detail-rientro").addEventListener("click", function () {
    var m = _movs.find(function (x) { return x.uid === _detailUid; }); if (m) openRientro(m);
  });
  if ($("ri-cancel")) $("ri-cancel").addEventListener("click", hideSheets);
  if ($("ri-save")) $("ri-save").addEventListener("click", function () {
    var m = _movs.find(function (x) { return x.uid === _rientroUid; }); if (!m) return;
    var ric = parseImporto($("ri-importo").value); if (ric <= 0) return;
    var upd = Object.assign({}, m, {
      importo_ricevuto: ric, data_ricevuto: $("ri-data").value || nowLocalInput(),
      wallet_to_uid: $("ri-wallet").value, giro_aperta: false,
      rev: (m.rev || 1) + 1, updated_at: new Date().toISOString(), _local: true
    });
    DB.put("movimenti", upd)
      .then(function () { return SYNC.getDeviceId().then(function (did) { return SYNC.recordOp("transaction", "upsert", upd, did); }); })
      .then(function () { hideSheets(); return render(); })
      .then(function () { return MIRROR.afterLocalChange(); });
  });

  // ---------- Detta o scrivi con l'AI (2c) ----------
  var _recog = null;
  function aiStatus(msg, kind) {
    var el = $("ai-status"); if (!el) return;
    el.hidden = !msg; el.textContent = msg || ""; el.className = "ai-status" + (kind ? " " + kind : "");
  }
  if ($("ai-btn")) $("ai-btn").addEventListener("click", function () {
    var box = $("ai-box"); if (!box) return;
    box.hidden = !box.hidden;
    if (!box.hidden && $("ai-text")) $("ai-text").focus();
  });
  if ($("ai-go")) $("ai-go").addEventListener("click", function () { interpretaTesto($("ai-text") ? $("ai-text").value : ""); });
  if ($("ai-mic")) $("ai-mic").addEventListener("click", function () { dettaVoce(); });

  function dettaVoce() {
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { aiStatus("La dettatura vocale non è disponibile qui: scrivi la frase e tocca Interpreta.", "warn"); return; }
    try {
      if (_recog) { try { _recog.stop(); } catch (e) {} }
      _recog = new SR();
      _recog.lang = "it-IT"; _recog.interimResults = true; _recog.maxAlternatives = 1;
      var mic = $("ai-mic");
      _recog.onstart = function () { aiStatus("Sto ascoltando… parla pure.", ""); if (mic) mic.classList.add("rec"); };
      _recog.onresult = function (e) {
        var txt = ""; for (var i = 0; i < e.results.length; i++) txt += e.results[i][0].transcript;
        if ($("ai-text")) $("ai-text").value = txt;
      };
      _recog.onerror = function (ev) { aiStatus("Non ho sentito bene" + (ev && ev.error ? " (" + ev.error + ")" : "") + ". Riprova o scrivi.", "warn"); if (mic) mic.classList.remove("rec"); };
      _recog.onend = function () { if (mic) mic.classList.remove("rec"); };
      _recog.start();
    } catch (e) { aiStatus("Dettatura non avviabile: scrivi la frase.", "warn"); }
  }

  function interpretaTesto(testo) {
    testo = (testo || "").trim();
    if (!testo) { aiStatus("Scrivi o detta una frase prima.", "warn"); return; }
    var base = apiBase();
    if (!base) { aiStatus("La detta-AI funziona quando il telefono raggiunge l'app (a casa, stessa rete del PC). Per ora scrivi il movimento a mano.", "warn"); return; }
    aiStatus("Sto interpretando…", "");
    var ctrl = new AbortController(); var to = setTimeout(function () { ctrl.abort(); }, 25000);
    fetch(base + "/api/finanze/parse", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ testo: testo }), signal: ctrl.signal
    }).then(function (r) { clearTimeout(to); if (!r.ok) throw new Error("http-" + r.status); return r.json(); })
      .then(function (p) {
        if (!p || !p.ok) { aiStatus(p && p.error === "no_key" ? "L'AI non è configurata sul PC." : "Non sono riuscito a interpretare. Prova a scriverlo più semplice.", "warn"); return; }
        applicaProposta(p);
        aiStatus("Fatto — controlla i campi qui sotto (confidenza " + (p.confidenza || "media") + ").", "ok");
      }).catch(function () {
        clearTimeout(to);
        aiStatus("Non raggiungo l'app (sei sulla stessa rete del PC?). Per ora scrivi a mano.", "warn");
      });
  }

  function applicaProposta(p) {
    popolaForm();
    setTipo(p.tipo || "uscita");
    var f = $("add-form");
    if (p.importo) f.importo.value = Number(p.importo).toLocaleString("it-IT", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (p.wallet_uid && _wallets.some(function (w) { return w.uid === p.wallet_uid; })) $("af-wallet").value = p.wallet_uid;
    if (p.tipo === "trasferimento" && p.wallet_to_uid) $("af-wallet-to").value = p.wallet_to_uid;
    if (p.tipo === "giro" && $("af-controparte")) $("af-controparte").value = p.controparte || "";
    if (p.tipo !== "trasferimento") f.categoria.value = p.categoria || "";
    if (p.data_local) $("af-data").value = String(p.data_local).slice(0, 16);
    f.descrizione.value = p.descrizione || "";
  }

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
          // Già collegato: nel modello a specchio "☁️ Drive" ri-controlla la copia
          // (auto-scarica se sicuro), NON fa la vecchia fusione.
          MIRROR.autoOnOpen();
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

  // ---------- Fase 3: copia a SPECCHIO (Drive) ----------
  /* Modello "una copia autorevole": UN file mirror.json fa da riferimento.
       Carica  = sovrascrivi mirror.json con il telefono (tenendo un backup);
       Scarica = rimpiazza TUTTO il telefono con mirror.json (sostituzione).
     Il vecchio sync a fusione (rete locale / ☁️ Drive) resta disponibile ma
     manuale. Invarianti di sicurezza per gli automatismi:
       - auto-scarica SOLO se hai già una base allineata, non sei "sporco"
         (nessuna modifica locale non ancora caricata) e sul Drive c'è di più
         nuovo → così non si perde mai una modifica locale non sincronizzata;
       - auto-carica SOLO dopo che il telefono ha una base (prima sincronizzazione
         esplicita) → così un telefono con dati sbagliati non sovrascrive il Drive. */
  var MIRROR = (function () {
    var _remoteNew = false, _autoTimer = null, _busy = false;

    function have() { return (typeof DRIVE !== "undefined") && !!$("mirror-pill"); }
    function meta() {
      return Promise.all([DB.getMeta("mirror_base_ts"), DB.getMeta("mirror_dirty"), DB.getMeta("mirror_seen_modified")])
        .then(function (r) { return { base: r[0] || "", dirty: !!r[1], seen: r[2] || "" }; });
    }
    function fmt(iso) { var d = new Date(iso); return isNaN(d) ? "" : d.toLocaleString(lang, { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }); }
    function setInfo(t) { if ($("mirror-info")) $("mirror-info").textContent = t; }
    // mostra il pulsante "Collega" oppure le azioni Carica/Scarica, secondo lo stato
    function showConn(connected) {
      if ($("drive-connect-row")) $("drive-connect-row").hidden = !!connected;
      if ($("mirror-actions")) $("mirror-actions").hidden = !connected;
    }

    function updatePill() {
      return meta().then(function (s) {
        var pill = $("mirror-pill"); if (!pill) return;
        if (s.dirty) { pill.hidden = false; pill.className = "pill up"; pill.textContent = "⬆︎ Da caricare"; }
        else if (_remoteNew) { pill.hidden = false; pill.className = "pill down"; pill.textContent = "⬇︎ Da scaricare"; }
        else { pill.hidden = true; }
      });
    }

    function buildMirror() {
      return SYNC.exportBundle().then(function (b) {
        var snap = b.snapshot;
        return {
          schema: 1, type: "mirror", ts: new Date().toISOString(), device: snap.device_id,
          counts: { w: (snap.wallets || []).length, c: (snap.categorie || []).length, m: (snap.movimenti || []).length },
          wallets: snap.wallets || [], categorie: snap.categorie || [], movimenti: snap.movimenti || []
        };
      });
    }

    function segnalaErrore(reason) {
      if (reason === "token") setInfo("Collega prima il tuo Google Drive (qui sopra).");
      else if (reason === "quota") setInfo("Spazio del Drive esaurito.");
      else setInfo("Non è riuscito (" + (reason || "errore") + "). Controlla la connessione al Drive.");
    }

    function afterAligned(baseTs, modifiedTime) {
      _remoteNew = false;
      return DB.setMeta("mirror_base_ts", baseTs)
        .then(function () { return DB.setMeta("mirror_dirty", ""); })
        .then(function () { return modifiedTime ? DB.setMeta("mirror_seen_modified", modifiedTime) : Promise.resolve(); });
    }

    // Carica: telefono → Drive (sovrascrive, con backup)
    function doUpload(manual) {
      if (_busy) return Promise.resolve(); _busy = true;
      if (manual) setInfo("Carico sul Drive…");
      return buildMirror().then(function (mirror) {
        return DRIVE.mirrorPush(mirror).then(function (res) {
          if (!res || !res.ok) { _busy = false; if (manual) segnalaErrore(res && res.reason); return; }
          // rileggo la modifiedTime reale del file appena scritto (per il confronto futuro)
          return DRIVE.mirrorStatus().then(function (st) {
            var mt = (st && st.ok && st.modifiedTime) ? st.modifiedTime : null;
            return afterAligned(mirror.ts, mt);
          }).then(function () {
            _busy = false;
            setInfo("Copia sul Drive aggiornata · " + fmt(mirror.ts));
            return updatePill();
          });
        });
      }).catch(function () { _busy = false; if (manual) segnalaErrore("errore"); });
    }

    // Scarica: Drive → telefono (sostituzione TOTALE)
    function doDownload(manual) {
      if (_busy) return Promise.resolve(); _busy = true;
      if (manual) setInfo("Scarico dal Drive…");
      return DRIVE.mirrorPull().then(function (res) {
        if (!res || !res.ok) { _busy = false; if (manual) segnalaErrore(res && res.reason); return; }
        if (!res.exists) { _busy = false; setInfo("Sul Drive non c'è ancora una copia: fai prima «Carica» (dal PC o da qui)."); return; }
        var snap = res.snap || {};
        if (!Array.isArray(snap.wallets)) { _busy = false; setInfo("La copia sul Drive non è leggibile."); return; }
        var quando = fmt(snap.ts) || (res.modifiedTime ? fmt(res.modifiedTime) : "");
        var n = (snap.movimenti || []).length;
        if (manual && !confirm("Sostituire TUTTO sul telefono con la copia dal Drive"
            + (quando ? " (del " + quando + ")" : "") + "?\n\n" + n + " movimenti verranno messi al posto di quelli attuali del telefono. "
            + "Sul Drive resta comunque un backup.")) {
          _busy = false; setInfo("Annullato."); return updatePill();
        }
        return DB.replaceData(snap)
          .then(resetSyncBookkeeping)
          .then(function () { return afterAligned(snap.ts || new Date().toISOString(), res.modifiedTime); })
          .then(function () { _busy = false; setInfo("Telefono allineato alla copia del Drive · " + (quando || "ora")); return render(); })
          .then(updatePill);
      }).catch(function () { _busy = false; if (manual) segnalaErrore("errore"); });
    }

    function resetSyncBookkeeping() {
      // Dopo una sostituzione totale azzera lo stato del vecchio sync a fusione
      // (il diario è già stato svuotato da replaceData) così i due modelli non litigano.
      return DB.setMeta("drive_seen", {})
        .then(function () { return DB.setMeta("drive_up_hash", ""); })
        .then(function () { return DB.setMeta("pc_diary_cursor", 0); })
        .then(function () { return DB.setMeta("needs_update", false); });
    }

    function refreshStatus() {
      return DRIVE.getToken().then(function (tok) {
        if (!tok) { _remoteNew = false; return { token: false }; }
        return DRIVE.mirrorStatus().then(function (st) {
          if (!st || !st.ok) return { token: true, exists: false };
          return meta().then(function (s) {
            _remoteNew = !!st.exists && !s.dirty && st.modifiedTime !== s.seen;
            return { token: true, exists: !!st.exists, modifiedTime: st.modifiedTime, state: s };
          });
        });
      });
    }

    function scheduleUpload() {
      if (_autoTimer) clearTimeout(_autoTimer);
      _autoTimer = setTimeout(function () {
        meta().then(function (s) {
          if (!s.base || !s.dirty) return;                          // gate: solo con base e se ancora "sporco"
          if (!navigator.onLine) return;
          DRIVE.getToken().then(function (tok) { if (tok) doUpload(false); });
        });
      }, 2500);
    }

    function afterLocalChange() {
      return DB.setMeta("mirror_dirty", "1").then(function () {
        _remoteNew = false;                                          // priorità al "da caricare"
        updatePill();
        scheduleUpload();
      });
    }

    function autoOnOpen() {
      if (!have()) return Promise.resolve();
      if ($("mirror-card")) $("mirror-card").hidden = false;
      return DRIVE.getToken().then(function (tok) {
        showConn(!!tok);
        if (!tok) { setInfo("Collega il tuo Google Drive per tenere telefono e PC allineati."); return updatePill(); }
        if (!navigator.onLine) { setInfo("Offline: la copia si sincronizza quando torni online."); return updatePill(); }
        return refreshStatus().then(function (info) {
          if (!info.exists) { setInfo("Sul Drive non c'è ancora una copia: fai «Carica» (dal PC o da qui)."); return updatePill(); }
          var s = info.state;
          // auto-scarica SOLO se sicuro: base presente, non sporco, e sul Drive è più nuovo
          if (s.base && !s.dirty && info.modifiedTime !== s.seen) return doDownload(false);
          // modifiche locali in sospeso con base già fatta → prova a ricaricare
          if (s.base && s.dirty) scheduleUpload();
          setInfo("Copia sul Drive · " + (fmt(info.modifiedTime) || "presente"));
          return updatePill();
        });
      }).catch(function () { return updatePill(); });
    }

    return {
      autoOnOpen: autoOnOpen, doUpload: doUpload, doDownload: doDownload,
      afterLocalChange: afterLocalChange, updatePill: updatePill, have: have
    };
  })();

  if ($("mirror-up")) $("mirror-up").addEventListener("click", function () { MIRROR.doUpload(true); });
  if ($("mirror-down")) $("mirror-down").addEventListener("click", function () { MIRROR.doDownload(true); });
  if ($("drive-recheck")) $("drive-recheck").addEventListener("click", function () { MIRROR.autoOnOpen(); });
  if ($("mirror-pill")) $("mirror-pill").addEventListener("click", function () {
    setTab("sync");
    DB.getMeta("mirror_dirty").then(function (d) { if (d) MIRROR.doUpload(true); else MIRROR.doDownload(true); });
  });

  // ---------- boot ----------
  segnalaRete();
  var driveBoot = HAS_DRIVE ? DRIVE.handleRedirect() : Promise.resolve(false);
  driveBoot.then(function (daGoogle) {
    if (daGoogle) setTab("sync");   // torni da Google: mostro l'esito nella scheda Sync
    return render().then(function () {
      // Modello a specchio: all'apertura si scarica dallo specchio (solo se sicuro).
      return MIRROR.autoOnOpen();
    });
  }).catch(function () {
    try { render(); } catch (e) {}
  });
})();
