# PIANO-FASE-5 — Collegamento a Google Drive (OAuth)

> Piano-contratto secondo WORKFLOW-AGENTI.md §4. Scritto da Claude Code (cervello)
> il 15/07/2026. Esecuzione: Claude Code (consentito da §1). Review: Claude Code.
> Contesto minimo: PIANO-V2.md §Fase 5, docs/SYNC-PROTOCOL.md (protocollo Fase 4).

## Obiettivo

Il telefono (PWA su Cloudflare) e il PC non si vedono via HTTP (HOST=127.0.0.1).
Il "corriere" è il Google Drive di Lorenzo: cartella nascosta **appDataFolder**,
scope minimo **`drive.appdata`** (l'app vede SOLO la sua cartellina, mai i file
di Drive). Ogni dispositivo carica il proprio stato e scarica quello degli altri;
la fusione usa il merge LWW già costruito e testato in Fase 4.

## Decisioni di architettura (vincolanti)

1. **Su Drive viaggia lo STATO completo per dispositivo**, non i diari a delta:
   un file `state-<device_id>.json` per dispositivo (formato = snapshot del
   protocollo, §5 di SYNC-PROTOCOL.md: schema, device_id, ts, wallets,
   categorie, movimenti — tombstone inclusi).
   Perché: (a) i dati sono pochi KB → il delta non serve; (b) i record creati
   PRIMA della Fase 4 non stanno nel diario del PC ma nello snapshot sì;
   (c) idempotente e auto-riparante (un file corrotto/perso si rigenera alla
   sync dopo); (d) le cancellazioni viaggiano comunque (tombstone nello stato).
   I diari locali restano e continuano ad alimentare la sync HTTP in LAN.
2. **Algoritmo di sync (identico sui due lati)** — `sync_once()`:
   1. lista i file `state-*.json` in appDataFolder;
   2. per ogni file di un ALTRO device: se `modifiedTime` è uguale all'ultimo
      visto (cursore locale) → salta; altrimenti scarica e applica come
      snapshot (merge LWW, ordine wallet→category→transaction);
   3. ricostruisce il proprio stato e lo carica (create o update);
      se l'hash del CONTENUTO (solo record, esclusi ts/diary_lines) è uguale
      all'ultimo upload e il file esiste già → non ricarica.
   Scaricare-prima-caricare-poi: lo stato caricato contiene già la fusione.
3. **PC — OAuth "installed app" con PKCE (S256)**, tutto con urllib stdlib
   (nessuna dipendenza nuova, coerente col vincolo "Yahoo via HTTP stdlib").
   Redirect di loopback direttamente sull'app FastAPI:
   `http://127.0.0.1:<porta>/impostazioni/drive/callback` (i client OAuth di
   tipo "Desktop" accettano qualunque porta di loopback senza registrarla).
   Credenziali (client id/secret) e token (refresh+access+scadenza) in
   `settings_store` → DB in `app/data/` (gitignorata). MAI nei log/repo.
4. **PWA — flusso implicit con redirect di pagina intera** (`response_type=token`),
   SENZA lo script Google gsi e SENZA popup (i popup nelle PWA standalone iOS
   sono inaffidabili). Il client OAuth è di tipo "Web application" con
   redirect URI = URL esatto della PWA. Token (~1h) in IndexedDB `meta`;
   alla scadenza il prossimo tap su Drive ripassa dal redirect (se la sessione
   Google è attiva è quasi istantaneo). Nessun client_secret nel browser
   (per design del flusso). Il client id lo incolla l'utente UNA volta nella
   PWA (salvato in IndexedDB): niente valori personali committati nel repo.
5. **Le credenziali le crea Lorenzo** (account suo): guida passo-passo in
   `docs/SETUP-DRIVE.md`. Consent screen in modalità Testing (uso personale).
6. **Test PRIMA del Drive vero** (regola PIANO-V2 §7): trasporto iniettabile
   (`DriveClient`), finto-Drive in memoria nei test.

## Task

### T1 — Motore PC: `app/shared/drive_sync.py` (nuovo)
- OAuth: `build_auth_url(redirect_uri)`, `handle_callback(code, state, redirect_uri)`,
  `get_access_token(force_refresh)` (refresh automatico; `invalid_grant` → token
  cancellato, dati locali intatti), `disconnect()` (revoca best-effort).
- Trasporto: classe `DriveClient` (list/download/upload su appDataFolder,
  multipart create + media update, urllib, timeout, errori tipizzati:
  `DriveAuthError` per 401/403, `DriveError` per il resto).
- Orchestrazione: `sync_once(client=None)` → dict
  `{ok, applied, skipped, errors, downloaded, uploaded, error}`;
  su 401 a metà sync: un solo retry con token rinnovato, poi errore pulito.
  Cursori (`drive_seen`), hash ultimo upload (`drive_last_upload_hash`) ed
  esito (`drive_last_sync`) in settings_store.
- Import dei dati remoti via `sync.apply_snapshot()` (già dentro `importing()`:
  niente eco nel diario, metadati sorgente preservati).
- Vincoli: nessuna nuova dipendenza; mai loggare token/credenziali; nessun
  dato finanziario nei log.

### T2 — Impostazioni PC: credenziali + collegamento + sync manuale
- `settings_store.KNOWN_SETTINGS` += `drive_client_id` (non segreto),
  `drive_client_secret` (segreto, mascherato).
- `settings_routes.py` += `GET /impostazioni/drive/connetti` (redirect a Google),
  `GET /impostazioni/drive/callback`, `POST /impostazioni/drive/sync`,
  `POST /impostazioni/drive/scollega`; la GET `/impostazioni` espone stato
  (configurato/collegato/ultima sync) e messaggi esito.
- `settings.html`: card "Google Drive" (stato, 2 campi credenziali, bottoni
  Collega / Sincronizza ora / Scollega, riga ultima sync, rimando alla guida).
- `i18n.py`: chiavi `set.drive_*` in it/en/es/fr/de/uk.
- `main.py`: all'avvio, in `_refresh_dati_bg`, sync best-effort se collegato
  (mai far fallire l'avvio).

### T3 — Client PWA: `pwa/drive.js` (nuovo) + integrazione
- `drive.js`: client id in meta; auth URL + `handleRedirect()` (parse del
  fragment, verifica `state`, pulizia URL); token in meta; REST Drive via
  fetch; `driveSync()` = stesso algoritmo di T1 (cursori in meta `drive_seen`,
  hash upload in meta); 401 → token cancellato, esito "ricollega".
- `sync.js`: estrai helper `opsFromSnapshot(snap)` (riusato da initialSync,
  importBundle e drive.js) — refactor senza cambi di comportamento.
- `index.html`: bottone "☁️ Drive" nel footer + mini-form una-tantum per il
  client id; `app.js`: wiring (setup → redirect → sync → render, stato in
  `#sync-info`); `sw.js`: cache v6 + `drive.js` negli ASSETS.

### T4 — Documentazione
- `docs/SETUP-DRIVE.md` (nuova): guida passo-passo per Lorenzo (progetto
  Google Cloud, Drive API, consent screen Testing + test user, client Desktop
  per il PC, client Web per la PWA, dove incollare cosa). Italiano semplice.
- `docs/SYNC-PROTOCOL.md`: nuova sezione §9 "Trasporto Google Drive".
- `PIANO-V2.md`: stato Fase 5.

### T5 — Test: `app/tests/test_drive_sync.py` (nuovo)
- FakeDrive in memoria (list/download/upload con modifiedTime e contatori).
- Casi minimi: prima sync carica lo stato; **X+Y** (stato remoto di un altro
  device → dopo sync il DB ha entrambi e lo stato ricaricato li contiene);
  remoto invariato → non riscarica; tombstone remota → record locale deleted;
  nessun cambiamento locale → non ricarica (hash); non connesso → errore
  pulito; callback con state sbagliato → rifiutata; refresh token (mock del
  token endpoint); DriveAuthError → esito `{ok:False, error:"auth"}`.

## Criteri di accettazione
1. `pytest app/tests/` verde al completo (24 esistenti + nuovi drive).
2. Senza credenziali configurate l'app è IDENTICA a prima (card Impostazioni
   mostra "da configurare", nessun errore, nessuna chiamata di rete).
3. Nessun segreto committato; token/credenziali solo in `app/data/` (DB) o
   IndexedDB; mai nei log.
4. La PWA si avvia ancora offline (drive.js non richiede rete al boot).
5. Il collaudo contro il Drive VERO richiede le credenziali di Lorenzo
   (docs/SETUP-DRIVE.md) + prova iPhone: è il criterio di fine della fase e
   resta in carico all'utente (io non posso creare account/credenziali).

## Fuori scope (rimandato)
- Compattazione/pulizia tombstone (Fase 7). Snapshot separato dal file di
  stato: non serve col modello a stato pieno. Sync periodica in background
  sul telefono (iOS non la consente alle PWA). Prezzi/notizie sul telefono
  (Fase 6).
