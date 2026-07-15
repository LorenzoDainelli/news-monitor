/* MyMoney PWA — sync via Google Drive (v2 Fase 5).
   Il Drive dell'utente fa da corriere: ogni dispositivo carica il proprio stato
   (state-<device_id>.json) nella cartella nascosta appDataFolder e scarica
   quello degli altri; la fusione usa il merge LWW di sync.js. Contratto in
   docs/SYNC-PROTOCOL.md §9, guida credenziali in docs/SETUP-DRIVE.md.

   Accesso: flusso OAuth "implicit" con redirect di PAGINA INTERA (niente popup,
   che nelle PWA standalone su iOS sono inaffidabili; niente script esterni).
   Il token (~1 ora) sta in IndexedDB; alla scadenza il prossimo tap su "Drive"
   ripassa dal redirect di Google (se la sessione è attiva, è quasi istantaneo).
   Scope minimo drive.appdata: l'app NON vede i file personali di Drive. */
window.DRIVE = (function () {
  "use strict";

  var SCOPE = "https://www.googleapis.com/auth/drive.appdata";
  var AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth";
  var API = "https://www.googleapis.com/drive/v3";
  var UPLOAD = "https://www.googleapis.com/upload/drive/v3";

  // ── client id (lo incolla l'utente una volta; vive solo in IndexedDB) ────
  function getClientId() { return DB.getMeta("drive_client_id"); }
  function setClientId(v) { return DB.setMeta("drive_client_id", (v || "").trim()); }

  // ── collegamento (redirect a Google e ritorno) ────────────────────────────
  function redirectUri() {
    /* URL esatto della pagina senza query/hash e senza "index.html": deve
       coincidere con il redirect URI registrato nel client OAuth (Web). */
    return (location.origin + location.pathname).replace(/index\.html$/, "");
  }

  function connect() {
    /* Naviga alla pagina di consenso Google. Da chiamare su tap dell'utente. */
    return getClientId().then(function (cid) {
      if (!cid) return false;
      var state = nuovoUid().substring(0, 16);
      try { sessionStorage.setItem("mm_drive_state", state); } catch (e) {}
      var params = new URLSearchParams({
        client_id: cid,
        redirect_uri: redirectUri(),
        response_type: "token",
        scope: SCOPE,
        state: state
      });
      location.href = AUTH_URL + "?" + params.toString();
      return true;
    });
  }

  function handleRedirect() {
    /* Al ritorno da Google il token è nel fragment (#access_token=…&state=…).
       Va chiamata SUBITO al boot: salva il token e pulisce l'URL.
       Ritorna Promise<bool> = "siamo appena tornati da Google". */
    var h = location.hash || "";
    if (h.indexOf("access_token=") === -1) return Promise.resolve(false);
    var q = new URLSearchParams(h.replace(/^#/, ""));
    var tok = q.get("access_token"), state = q.get("state");
    var atteso = null;
    try {
      atteso = sessionStorage.getItem("mm_drive_state");
      sessionStorage.removeItem("mm_drive_state");
    } catch (e) {}
    history.replaceState(null, "", location.pathname + location.search);
    // Verifica lo state se ce l'abbiamo ancora (protezione da token estranei);
    // se sessionStorage si è perso nel giro (quirk iOS) accettiamo comunque.
    if (!tok || (atteso && state !== atteso)) return Promise.resolve(false);
    var scadenza = Date.now() + (parseInt(q.get("expires_in") || "3600", 10) - 60) * 1000;
    return DB.setMeta("drive_token", { t: tok, exp: scadenza }).then(function () { return true; });
  }

  function getToken() {
    return DB.getMeta("drive_token").then(function (tk) {
      return (tk && tk.t && Date.now() < tk.exp) ? tk.t : null;
    });
  }

  function clearToken() { return DB.setMeta("drive_token", null); }

  // ── REST Drive (fetch; 401 → {code:"auth"}) ───────────────────────────────
  function api(token, method, url, body, ctype) {
    var headers = { Authorization: "Bearer " + token };
    if (ctype) headers["Content-Type"] = ctype;
    return fetch(url, { method: method, headers: headers, body: body || undefined })
      .then(function (res) {
        if (res.status === 401) throw { code: "auth" };
        if (!res.ok) {
          if (res.status === 403) {
            return res.text().then(function (txt) {
              if (txt.indexOf("storageQuota") !== -1 || txt.indexOf("quotaExceeded") !== -1) throw { code: "quota" };
              throw { code: "http_" + res.status };
            });
          }
          throw { code: "http_" + res.status };
        }
        return res;
      });
  }

  function listFiles(token) {
    var u = API + "/files?spaces=appDataFolder&pageSize=100&fields=" +
      encodeURIComponent("files(id,name,modifiedTime)");
    return api(token, "GET", u).then(function (r) { return r.json(); })
      .then(function (d) { return d.files || []; });
  }

  function download(token, id) {
    return api(token, "GET", API + "/files/" + id + "?alt=media")
      .then(function (r) { return r.json(); });
  }

  function upload(token, name, data, fileId) {
    var content = JSON.stringify(data);
    if (fileId) {
      return api(token, "PATCH", UPLOAD + "/files/" + fileId + "?uploadType=media",
                 content, "application/json");
    }
    var boundary = "mm" + nuovoUid().substring(0, 12);
    var body = "--" + boundary + "\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n" +
      JSON.stringify({ name: name, parents: ["appDataFolder"] }) +
      "\r\n--" + boundary + "\r\nContent-Type: application/json\r\n\r\n" +
      content + "\r\n--" + boundary + "--";
    return api(token, "POST", UPLOAD + "/files?uploadType=multipart",
               body, "multipart/related; boundary=" + boundary);
  }

  // ── impronta dello stato (per non ricaricare se nulla è cambiato) ─────────
  function canonical(obj) {
    if (obj === null || typeof obj !== "object") return JSON.stringify(obj);
    if (Array.isArray(obj)) return "[" + obj.map(canonical).join(",") + "]";
    return "{" + Object.keys(obj).sort().map(function (k) {
      return JSON.stringify(k) + ":" + canonical(obj[k]);
    }).join(",") + "}";
  }

  function stateHash(snap) {
    /* Solo il CONTENUTO (record ordinati per uid): ts cambia a ogni chiamata.
       Confrontata solo con se stessa sul device: basta un hash semplice. */
    var byUid = function (a, b) { return (a.uid || "") < (b.uid || "") ? -1 : 1; };
    var canon = canonical({
      wallets: (snap.wallets || []).slice().sort(byUid),
      categorie: (snap.categorie || []).slice().sort(byUid),
      movimenti: (snap.movimenti || []).slice().sort(byUid)
    });
    var h = 5381;
    for (var i = 0; i < canon.length; i++) h = ((h << 5) + h + canon.charCodeAt(i)) | 0;
    return h + ":" + canon.length;
  }

  // ── la sync vera e propria (stesso algoritmo del PC) ─────────────────────
  function driveSync() {
    /* 1. lista i file state-*.json; 2. scarica e fondi quelli degli ALTRI
       device (salta gli invariati per modifiedTime); 3. ricarica il proprio
       stato (che ora include la fusione), se davvero cambiato. */
    return getToken().then(function (token) {
      if (!token) return { ok: false, reason: "token" };
      return Promise.all([SYNC.getDeviceId(), DB.getMeta("drive_seen"), DB.getMeta("drive_up_hash")])
        .then(function (r) {
          var deviceId = r[0], seen = r[1] || {}, lastHash = r[2] || "";
          var mine = "state-" + deviceId + ".json";
          var stats = { applied: 0, downloaded: 0, future: 0 };

          return listFiles(token).then(function (files) {
            var daScaricare = files.filter(function (f) {
              return f.name && f.name.indexOf("state-") === 0 && /\.json$/.test(f.name)
                && f.name !== mine && seen[f.name] !== f.modifiedTime;
            });
            var p = Promise.resolve();
            daScaricare.forEach(function (f) {
              p = p.then(function () {
                return download(token, f.id).then(function (snap) {
                  if (!snap) return;
                  if (snap.schema > 1) {
                    // Schema più nuovo: NON marcare 'seen' (verrà riletto dopo
                    // l'aggiornamento dell'app) e alza l'avviso.
                    stats.future++;
                    return DB.setMeta("needs_update", true);
                  }
                  return SYNC.applyRemoteOps(SYNC.opsFromSnapshot(snap), deviceId)
                    .then(function (res) {
                      stats.applied += res.applied;
                      stats.downloaded++;
                      seen[f.name] = f.modifiedTime;
                    });
                });
              });
            });

            return p.then(function () { return SYNC.exportBundle(); }).then(function (bundle) {
              var snap = bundle.snapshot;
              var hash = stateHash(snap);
              var existing = files.filter(function (f) { return f.name === mine; })[0];
              var upP = (existing && hash === lastHash)
                ? Promise.resolve(false)
                : upload(token, mine, snap, existing ? existing.id : null)
                    .then(function () { return DB.setMeta("drive_up_hash", hash); })
                    .then(function () { return true; });
              return upP.then(function (uploaded) {
                // Sync pulita (nessuno stato di schema più nuovo) → spegni
                // l'avviso "aggiorna" (auto-guarigione dopo un aggiornamento).
                var healP = stats.future === 0 ? DB.setMeta("needs_update", false) : Promise.resolve();
                return healP
                  .then(function () { return DB.setMeta("drive_seen", seen); })
                  .then(function () { return DB.setMeta("last_sync", new Date().toISOString()); })
                  .then(function () {
                    return { ok: true, applied: stats.applied,
                             downloaded: stats.downloaded, uploaded: uploaded };
                  });
              });
            });
          });
        });
    }).catch(function (err) {
      if (err && err.code === "auth") {
        // Token scaduto/revocato: dimenticalo; il prossimo tap ripassa da Google.
        return clearToken().then(function () { return { ok: false, reason: "token" }; });
      }
      return { ok: false, reason: (err && err.code) || (err && err.message) || "errore" };
    });
  }

  return {
    getClientId: getClientId,
    setClientId: setClientId,
    connect: connect,
    handleRedirect: handleRedirect,
    getToken: getToken,
    driveSync: driveSync
  };
})();
