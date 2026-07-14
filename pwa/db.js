/* MyMoney PWA — archivio locale (IndexedDB). v2 Fase 4.
   Tiene sul telefono i dati delle Finanze (portafogli, categorie, movimenti) così
   l'app funziona OFFLINE. Ogni record porta i metadati di sync (uid/rev/updated_at/
   deleted), gli stessi del PC: pronti per la sincronizzazione.
   Chiave primaria di ogni store = uid (stabile tra dispositivi).

   Fase 4: aggiunto store `diary` (append-only, autoincrement) per le operazioni
   locali da sincronizzare. Schema versione 2. */
window.DB = (function () {
  "use strict";
  var NAME = "mymoney", VERSION = 2;
  var _db = null;

  function open() {
    if (_db) return Promise.resolve(_db);
    return new Promise(function (resolve, reject) {
      var req = indexedDB.open(NAME, VERSION);
      req.onupgradeneeded = function (e) {
        var db = req.result;
        var old = e.oldVersion;
        // v1: store base
        if (old < 1) {
          if (!db.objectStoreNames.contains("wallets")) db.createObjectStore("wallets", { keyPath: "uid" });
          if (!db.objectStoreNames.contains("categorie")) db.createObjectStore("categorie", { keyPath: "uid" });
          if (!db.objectStoreNames.contains("movimenti")) db.createObjectStore("movimenti", { keyPath: "uid" });
          if (!db.objectStoreNames.contains("meta")) db.createObjectStore("meta", { keyPath: "k" });
        }
        // v2: diario sync (Fase 4)
        if (old < 2) {
          if (!db.objectStoreNames.contains("diary")) {
            var ds = db.createObjectStore("diary", { keyPath: "id", autoIncrement: true });
            ds.createIndex("pushed", "_pushed", { unique: false });
          }
        }
      };
      req.onsuccess = function () { _db = req.result; resolve(_db); };
      req.onerror = function () { reject(req.error); };
    });
  }

  function tx(store, mode) {
    return open().then(function (db) {
      return db.transaction(store, mode).objectStore(store);
    });
  }
  function wrap(request) {
    return new Promise(function (resolve, reject) {
      request.onsuccess = function () { resolve(request.result); };
      request.onerror = function () { reject(request.error); };
    });
  }

  return {
    getAll: function (store) { return tx(store, "readonly").then(function (s) { return wrap(s.getAll()); }); },
    get: function (store, key) { return tx(store, "readonly").then(function (s) { return wrap(s.get(key)); }); },
    put: function (store, obj) { return tx(store, "readwrite").then(function (s) { return wrap(s.put(obj)); }); },
    putMany: function (store, arr) {
      return open().then(function (db) {
        return new Promise(function (resolve, reject) {
          var t = db.transaction(store, "readwrite"), os = t.objectStore(store);
          (arr || []).forEach(function (o) { os.put(o); });
          t.oncomplete = function () { resolve(true); };
          t.onerror = function () { reject(t.error); };
        });
      });
    },
    del: function (store, key) { return tx(store, "readwrite").then(function (s) { return wrap(s.delete(key)); }); },
    clear: function (store) { return tx(store, "readwrite").then(function (s) { return wrap(s.clear()); }); },
    getMeta: function (k) { return this.get("meta", k).then(function (r) { return r ? r.v : null; }); },
    setMeta: function (k, v) { return this.put("meta", { k: k, v: v }); },
    isEmpty: function () {
      return this.getAll("wallets").then(function (ws) { return !ws || ws.length === 0; });
    },

    // ── Fase 4: diario sync ────────────────────────────────────────────
    appendDiary: function (entry) {
      return tx("diary", "readwrite").then(function (s) { return wrap(s.add(entry)); });
    },
    getAllDiary: function () {
      return tx("diary", "readonly").then(function (s) { return wrap(s.getAll()); });
    },
    getUnpushedDiary: function () {
      return tx("diary", "readonly").then(function (s) {
        return wrap(s.index("pushed").getAll(false));
      });
    },
    markDiaryPushed: function (ids) {
      return open().then(function (db) {
        return new Promise(function (resolve, reject) {
          var t = db.transaction("diary", "readwrite"), os = t.objectStore("diary");
          ids.forEach(function (id) {
            var req = os.get(id);
            req.onsuccess = function () {
              var entry = req.result;
              if (entry) { entry._pushed = true; os.put(entry); }
            };
          });
          t.oncomplete = function () { resolve(true); };
          t.onerror = function () { reject(t.error); };
        });
      });
    }
  };
})();

/* uid nuovo (32 hex), come sul PC. Usa crypto.randomUUID se c'è, con ripiego. */
window.nuovoUid = function () {
  try {
    if (crypto && crypto.randomUUID) return crypto.randomUUID().replace(/-/g, "");
  } catch (e) {}
  var s = "";
  for (var i = 0; i < 32; i++) s += Math.floor(Math.random() * 16).toString(16);
  return s;
};
