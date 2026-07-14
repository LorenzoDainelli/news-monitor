/* MyMoney PWA — motore di sincronizzazione (v2 Fase 4).
   Protocollo stile Cashew: diario locale + merge LWW + push/pull via API HTTP.
   Il contratto è in docs/SYNC-PROTOCOL.md.

   Flusso:
   1. Ogni operazione locale (aggiungi/modifica/elimina) scrive nel diario IndexedDB
   2. fullSync(): push → POST /api/finanze/ops (invia le ops locali non pushate)
                  pull → GET /api/finanze/diary?since=N (scarica ops del PC)
   3. Le ops remote vengono applicate in locale con merge LWW (stesse regole del PC) */
window.SYNC = (function () {
  "use strict";

  // ── device id ────────────────────────────────────────────────────────────
  function getDeviceId() {
    return DB.getMeta("device_id").then(function (id) {
      if (id) return id;
      var newId = "pwa_" + nuovoUid().substring(0, 12);
      return DB.setMeta("device_id", newId).then(function () { return newId; });
    });
  }

  // ── registrazione nel diario ─────────────────────────────────────────────
  function recordOp(entity, op, fields, deviceId) {
    var entry = {
      schema: 1,
      uid: fields.uid,
      entity: entity,
      op: op,
      fields: fields,
      rev: fields.rev || 1,
      updated_at: fields.updated_at || new Date().toISOString(),
      device_id: deviceId,
      ts: new Date().toISOString(),
      _pushed: false    // false = non ancora inviato al PC
    };
    return DB.appendDiary(entry);
  }

  // ── merge LWW ────────────────────────────────────────────────────────────
  function _wins(remoteRev, remoteUpdated, remoteDevice,
                 localRev, localUpdated, localDevice) {
    /* Vince il più alto: (rev, updated_at, device_id) */
    var rr = remoteRev || 0, lr = localRev || 0;
    if (rr !== lr) return rr > lr;
    var ru = String(remoteUpdated || ""), lu = String(localUpdated || "");
    if (ru !== lu) return ru > lu;
    return String(remoteDevice || "") > String(localDevice || "");
  }

  function _applyFields(existing, entity, fields, stores) {
    /* Sovrascrive i campi del record locale con quelli remoti */
    var obj = existing || {};
    obj.uid = fields.uid;
    obj.rev = fields.rev || 1;
    obj.updated_at = fields.updated_at;
    obj.deleted = !!fields.deleted;

    if (entity === "wallet") {
      obj.nome = fields.nome || "";
      obj.tipo = fields.tipo || "altro";
      obj.saldo_iniziale = fields.saldo_iniziale || 0;
      obj.note = fields.note || "";
      obj.ordine = fields.ordine || 0;
      obj.archiviato = !!fields.archiviato;
      obj.colore = fields.colore || "";
    } else if (entity === "category") {
      obj.nome = fields.nome || "";
      obj.kind = fields.kind || "";
      obj.archiviato = !!fields.archiviato;
    } else if (entity === "transaction") {
      obj.tipo = fields.tipo || "uscita";
      obj.data = fields.data;
      obj.importo = fields.importo || 0;
      obj.wallet_uid = fields.wallet_uid || null;
      obj.wallet_to_uid = fields.wallet_to_uid || null;
      obj.categoria_uid = fields.categoria_uid || null;
      obj.descrizione = fields.descrizione || "";
      obj.giro_id = fields.giro_id || "";
      obj.giro_aperta = !!fields.giro_aperta;
      obj.importo_ricevuto = fields.importo_ricevuto != null ? fields.importo_ricevuto : null;
      obj.data_ricevuto = fields.data_ricevuto || null;
      obj.controparte = fields.controparte || "";
    }
    return obj;
  }

  var ENTITY_STORE = { wallet: "wallets", category: "categorie", transaction: "movimenti" };

  function applyRemoteOps(ops, localDeviceId) {
    /* Applica le operazioni remote in locale con merge LWW.
       Ordine: wallet → category → transaction (per FK). */
    var byEntity = { wallet: [], category: [], transaction: [] };
    (ops || []).forEach(function (op) {
      var e = op.entity;
      if (byEntity[e]) byEntity[e].push(op);
    });

    var applied = 0, skipped = 0;
    var order = ["wallet", "category", "transaction"];

    // Promesse sequenziali per rispettare l'ordine
    var p = Promise.resolve();
    order.forEach(function (entity) {
      byEntity[entity].forEach(function (op) {
        p = p.then(function () {
          var store = ENTITY_STORE[entity];
          var uid = op.uid;
          var fields = op.fields || {};
          return DB.get(store, uid).then(function (local) {
            if (local) {
              // Record esiste: chi vince?
              if (!_wins(op.rev, op.updated_at, op.device_id,
                         local.rev, local.updated_at, localDeviceId)) {
                skipped++;
                return;
              }
            }
            // Remoto vince (o record nuovo): applica
            var obj = _applyFields(local, entity, fields);
            applied++;
            return DB.put(store, obj);
          });
        });
      });
    });

    return p.then(function () {
      return { applied: applied, skipped: skipped };
    });
  }

  // ── push: invia ops locali non pushate al PC ────────────────────────────
  function pushToPC(apiBase) {
    return Promise.all([getDeviceId(), DB.getUnpushedDiary()]).then(function (r) {
      var deviceId = r[0], ops = r[1];
      if (!ops.length) return { pushed: 0 };
      var body = { schema: 1, device_id: deviceId, ops: ops.map(function (o) {
        var copy = {}; for (var k in o) { if (k !== "_pushed" && k !== "id") copy[k] = o[k]; }
        return copy;
      }) };
      var ctrl = new AbortController();
      var to = setTimeout(function () { ctrl.abort(); }, 10000);
      return fetch(apiBase + "/api/finanze/ops", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: ctrl.signal
      }).then(function (res) {
        clearTimeout(to);
        if (!res.ok) throw new Error("push-http-" + res.status);
        return res.json();
      }).then(function (data) {
        if (!data.ok) throw new Error("push-rejected");
        // Marca le ops come pushate
        return DB.markDiaryPushed(ops.map(function (o) { return o.id; })).then(function () {
          return { pushed: ops.length, serverLines: data.diary_lines };
        });
      });
    });
  }

  // ── pull: scarica ops del PC e applicale ─────────────────────────────────
  function pullFromPC(apiBase) {
    return Promise.all([getDeviceId(), DB.getMeta("pc_diary_cursor")]).then(function (r) {
      var deviceId = r[0], cursor = r[1] || 0;
      var ctrl = new AbortController();
      var to = setTimeout(function () { ctrl.abort(); }, 10000);
      return fetch(apiBase + "/api/finanze/diary?since=" + cursor, {
        signal: ctrl.signal,
        headers: { Accept: "application/json" }
      }).then(function (res) {
        clearTimeout(to);
        if (!res.ok) throw new Error("pull-http-" + res.status);
        return res.json();
      }).then(function (data) {
        if (!data.ok) return { applied: 0, skipped: 0 };
        return applyRemoteOps(data.ops, deviceId).then(function (result) {
          // Aggiorna il cursore
          return DB.setMeta("pc_diary_cursor", data.total_lines).then(function () {
            return result;
          });
        });
      });
    });
  }

  // ── primo avvio: snapshot ────────────────────────────────────────────────
  function initialSync(apiBase) {
    return getDeviceId().then(function (deviceId) {
      var ctrl = new AbortController();
      var to = setTimeout(function () { ctrl.abort(); }, 15000);
      return fetch(apiBase + "/api/finanze/snapshot", {
        signal: ctrl.signal,
        headers: { Accept: "application/json" }
      }).then(function (res) {
        clearTimeout(to);
        if (!res.ok) throw new Error("snapshot-http-" + res.status);
        return res.json();
      }).then(function (snap) {
        // Lo snapshot è una lista di record: applicali come ops
        var ops = [];
        ["wallets", "categorie", "movimenti"].forEach(function (key) {
          var entity = { wallets: "wallet", categorie: "category", movimenti: "transaction" }[key];
          (snap[key] || []).forEach(function (fields) {
            ops.push({
              schema: 1, uid: fields.uid, entity: entity,
              op: fields.deleted ? "delete" : "upsert",
              fields: fields, rev: fields.rev || 1,
              updated_at: fields.updated_at || "",
              device_id: snap.device_id || ""
            });
          });
        });
        return applyRemoteOps(ops, deviceId);
      });
    });
  }

  // ── sync completa: push + pull ───────────────────────────────────────────
  function fullSync(apiBase) {
    if (!navigator.onLine) return Promise.resolve({ ok: false, reason: "offline" });
    return DB.isEmpty().then(function (empty) {
      if (empty) {
        // Primo avvio: scarica lo snapshot
        return initialSync(apiBase).then(function (result) {
          return DB.setMeta("last_sync", new Date().toISOString()).then(function () {
            return { ok: true, initial: true, applied: result.applied };
          });
        });
      }
      // Sync normale: push poi pull
      return pushToPC(apiBase).then(function (pushResult) {
        return pullFromPC(apiBase).then(function (pullResult) {
          return DB.setMeta("last_sync", new Date().toISOString()).then(function () {
            return {
              ok: true,
              pushed: pushResult.pushed,
              applied: pullResult.applied,
              skipped: pullResult.skipped
            };
          });
        });
      });
    }).catch(function (err) {
      return { ok: false, reason: err.message || "errore" };
    });
  }

  // ── export/import manuale ────────────────────────────────────────────────
  function exportBundle() {
    return Promise.all([
      DB.getAll("wallets"), DB.getAll("categorie"), DB.getAll("movimenti"),
      getDeviceId(), DB.getAllDiary()
    ]).then(function (r) {
      return {
        schema: 1, type: "bundle",
        snapshot: {
          schema: 1, device_id: r[3],
          ts: new Date().toISOString(),
          wallets: r[0], categorie: r[1], movimenti: r[2]
        },
        diary: r[4].map(function (o) {
          var copy = {}; for (var k in o) { if (k !== "_pushed" && k !== "id") copy[k] = o[k]; }
          return copy;
        })
      };
    });
  }

  function importBundle(data) {
    return getDeviceId().then(function (deviceId) {
      var ops = [];
      var snap = data.snapshot || data;
      ["wallets", "categorie", "movimenti"].forEach(function (key) {
        var entity = { wallets: "wallet", categorie: "category", movimenti: "transaction" }[key];
        (snap[key] || []).forEach(function (fields) {
          ops.push({
            schema: 1, uid: fields.uid, entity: entity,
            op: fields.deleted ? "delete" : "upsert",
            fields: fields, rev: fields.rev || 1,
            updated_at: fields.updated_at || "",
            device_id: snap.device_id || ""
          });
        });
      });
      // Poi il diario (se presente)
      (data.diary || []).forEach(function (op) { ops.push(op); });
      return applyRemoteOps(ops, deviceId);
    });
  }

  return {
    getDeviceId: getDeviceId,
    recordOp: recordOp,
    applyRemoteOps: applyRemoteOps,
    fullSync: fullSync,
    pushToPC: pushToPC,
    pullFromPC: pullFromPC,
    initialSync: initialSync,
    exportBundle: exportBundle,
    importBundle: importBundle
  };
})();
