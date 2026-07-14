# Protocollo di sincronizzazione MyMoney (v1)

Contratto tra il PC (Python/SQLAlchemy) e la PWA (JavaScript/IndexedDB).
**Stile Cashew**: diario append-only per dispositivo, merge last-write-wins per record.

## Schema: 1

Ogni messaggio dichiara `"schema": 1`. Se in futuro cambiamo il formato, i
dispositivi non aggiornati ignorano le versioni che non comprendono.

---

## 1. Entità sincronizzate

| Entità       | Chiave primaria sync | Campi dati                                                                                             |
|--------------|----------------------|--------------------------------------------------------------------------------------------------------|
| `wallet`     | `uid` (hex 32)       | nome, tipo, saldo_iniziale, note, ordine, archiviato, colore                                          |
| `category`   | `uid` (hex 32)       | nome, kind, archiviato                                                                                |
| `transaction`| `uid` (hex 32)       | tipo, data, importo, wallet_uid, wallet_to_uid, categoria_uid, descrizione, giro_id, giro_aperta, importo_ricevuto, data_ricevuto, controparte |

Ogni record porta anche i **metadati di sync**: `rev`, `updated_at`, `deleted`.

I riferimenti tra record (wallet_uid, wallet_to_uid, categoria_uid) usano **sempre
lo `uid`** dell'entità referenziata, mai l'id interno (che varia tra dispositivi).

---

## 2. Formato diario (JSONL)

Ogni dispositivo tiene un diario locale, un file append-only in formato JSONL
(una riga JSON per operazione):

```
<app/data/sync>/changes-<device_id>.jsonl
```

Ogni riga:

```json
{
  "schema": 1,
  "uid": "a1b2c3d4e5f6...",
  "entity": "transaction",
  "op": "upsert",
  "fields": {
    "uid": "a1b2c3d4e5f6...",
    "tipo": "uscita",
    "data": "2026-07-13T14:30:00",
    "importo": 20.0,
    "wallet_uid": "f1e2d3c4b5a6...",
    "wallet_to_uid": null,
    "categoria_uid": "abcdef123456...",
    "descrizione": "Benzina",
    "giro_id": "",
    "giro_aperta": false,
    "importo_ricevuto": null,
    "data_ricevuto": null,
    "controparte": "",
    "deleted": false,
    "rev": 1,
    "updated_at": "2026-07-13T14:30:00"
  },
  "rev": 1,
  "updated_at": "2026-07-13T14:30:00",
  "device_id": "pc_a1b2c3d4e5f6",
  "ts": "2026-07-13T14:30:00.123456"
}
```

| Campo        | Tipo     | Descrizione                                                   |
|--------------|----------|---------------------------------------------------------------|
| `schema`     | int      | Versione del protocollo (sempre 1 per ora)                   |
| `uid`        | string   | UID del record (chiave primaria sync, identità stabile)       |
| `entity`     | string   | `"wallet"` \| `"category"` \| `"transaction"`                |
| `op`         | string   | `"upsert"` (crea o aggiorna) \| `"delete"` (tombstone)       |
| `fields`     | object   | Tutti i campi del record, inclusi rev/updated_at/deleted      |
| `rev`        | int      | Versione del record (duplicata dal campo in fields)           |
| `updated_at` | string   | ISO-8601, ultima modifica (duplicata per quick-lookup)        |
| `device_id`  | string   | Identificativo del dispositivo che ha generato l'operazione   |
| `ts`         | string   | ISO-8601, timestamp di quando la riga è stata scritta nel diario |

### Op `"delete"`

Una cancellazione NON rimuove la riga fisicamente. Viene scritto un `upsert` con
`fields.deleted = true` (tombstone). L'`op` è `"delete"` per chiarezza, ma il
merge la tratta come un upsert di un record con `deleted=true`.

---

## 3. Regole di merge (LWW per record)

Quando un dispositivo riceve un'operazione da un altro dispositivo:

1. Cerca il record locale con lo stesso `uid`
2. Se **non esiste** → inserisci il record con i valori di `fields`
3. Se **esiste** → confronta per decidere chi vince:

### Ordinamento di vittoria

Vince il record con il valore **più alto** nella sequenza:

```
(rev, updated_at, device_id)
```

- `rev` più alto vince (intero, confronto numerico)
- A parità di `rev`, `updated_at` più recente vince (stringa ISO-8601, confronto lessicografico)
- A ulteriore parità, `device_id` più alto vince (stringa, confronto lessicografico)

Se il record **remoto vince** → sovrascrivi tutti i campi locali con quelli remoti.
Se il record **locale vince** → ignora l'operazione remota (skip).

### Tombstone

Un record con `deleted=true` è un **tombstone**: partecipa al merge normalmente.
Se il tombstone ha `rev` più alto, vince e il record locale diventa `deleted=true`.
I tombstone non vengono mai rimossi dal merge; la compattazione (futura) se ne
occupa quando lo snapshot li ha incorporati.

### Idempotenza

Reimportare lo stesso diario (o parte di esso) non crea duplicati: il confronto
(rev, updated_at, device_id) è deterministico e un'operazione già applicata viene
skippata.

---

## 4. Ordine di applicazione

Quando si importano operazioni, vanno applicate in quest'ordine:

1. **wallet** (prima, perché transaction li referenzia)
2. **category** (poi, stessa ragione)
3. **transaction** (ultima, le FK sono già risolte)

All'interno di ogni entità, l'ordine non conta (ogni record è indipendente).

---

## 5. Formato snapshot

Una fotografia completa dello stato, usata per il primo avvio di un dispositivo
nuovo o per un reset:

```json
{
  "schema": 1,
  "device_id": "pc_a1b2c3d4e5f6",
  "ts": "2026-07-13T14:30:00.123456",
  "diary_lines": 142,
  "wallets": [ { ... campi completi ... } ],
  "categorie": [ { ... campi completi ... } ],
  "movimenti": [ { ... campi completi ... } ]
}
```

Ogni record nello snapshot ha gli stessi campi di `fields` nel diario. Un
dispositivo che riceve uno snapshot lo applica come una serie di upsert (con le
stesse regole di merge LWW), così non sovrascrive dati più recenti.

`diary_lines` è il numero di righe del diario del PC al momento dello snapshot:
il client lo salva come cursore iniziale (`pc_diary_cursor`), così la prima sync
normale scarica solo le operazioni NUOVE invece di ri-scaricare l'intero diario
(che sarebbe comunque idempotente, ma inutile).

**Nota sui timestamp:** `updated_at` viaggia come stringa ISO-8601. Il telefono
la produce in UTC (`…Z`), il PC in ora locale; in import il PC normalizza sempre
a `datetime` **naive** (nessun mix naive/aware nel database). Il confronto di
merge resta comunque **deterministico e convergente** su entrambi i lati perché
`rev` è la chiave primaria e `updated_at` interviene solo a parità di `rev`.

---

## 6. API HTTP (sync PC ↔ PWA in LAN)

### `POST /api/finanze/ops`

La PWA invia le sue operazioni al PC.

**Request:**
```json
{
  "schema": 1,
  "device_id": "pwa_b2c3d4e5f6a1",
  "ops": [ ... righe diario ... ]
}
```

**Response:**
```json
{
  "ok": true,
  "applied": 5,
  "skipped": 2,
  "errors": 0,
  "server_device_id": "pc_a1b2c3d4e5f6",
  "diary_lines": 142
}
```

`diary_lines` = numero totale di righe nel diario del server (il client lo usa
come cursore per il pull successivo).

### `GET /api/finanze/diary?since=<N>`

Il client scarica il diario del PC dal cursore `N` in poi.

**Response:**
```json
{
  "ok": true,
  "device_id": "pc_a1b2c3d4e5f6",
  "since": 100,
  "ops": [ ... righe diario ... ],
  "total_lines": 142
}
```

### `GET /api/finanze/snapshot`

Fotografia completa (per primo avvio).

**Response:** l'oggetto snapshot come descritto nella sezione 5.

### `GET /api/finanze/export`

Scarica un file JSON con snapshot + diario (backup/fallback).

### `POST /api/finanze/import`

Carica un file JSON di export da un altro dispositivo.

---

## 7. Device ID

Ogni dispositivo genera un ID unico al primo avvio:

- **PC**: `"pc_" + uuid4().hex[:12]` — salvato in `settings_store` (chiave `sync_device_id`)
- **PWA**: `"pwa_" + crypto.randomUUID()[:12]` — salvato in IndexedDB (store `meta`, chiave `device_id`)

Il device_id è stabile: una volta generato, non cambia mai.

---

## 8. Flusso di sync

```
PWA                                     PC
 │                                       │
 │  1. POST /api/finanze/ops             │
 │  ──────────────────────────────────▶  │  Applica ops PWA (merge LWW)
 │                                       │  Ritorna {applied, diary_lines}
 │  ◀──────────────────────────────────  │
 │                                       │
 │  2. GET /api/finanze/diary?since=N    │
 │  ──────────────────────────────────▶  │  Ritorna ops PC dal cursore N
 │  ◀──────────────────────────────────  │
 │                                       │
 │  3. Applica ops PC in locale (LWW)    │
 │  4. Aggiorna cursore locale           │
 │  5. Re-render UI                      │
```

Il primo avvio usa `GET /api/finanze/snapshot` al posto del passo 2.

---

## 9. Trasporto Google Drive (Fase 5)

Quando PC e telefono non si vedono via HTTP (il server gira su 127.0.0.1), il
"corriere" è il Google Drive dell'utente: cartella nascosta **appDataFolder**,
scope minimo `drive.appdata` (l'app vede solo la sua cartellina).

### File su Drive

Un file per dispositivo, con lo **stato completo** (formato snapshot, §5):

```
state-<device_id>.json
```

Perché lo stato pieno e non i diari a delta: i dati sono pochi KB; lo snapshot
contiene anche i record nati prima della Fase 4 (che nel diario del PC non ci
sono); il formato è idempotente e auto-riparante (un file perso o corrotto si
rigenera alla sync successiva); i tombstone viaggiano comunque (`deleted=true`
resta nello stato fino alla compattazione, Fase 7). I diari locali restano e
continuano ad alimentare la sync HTTP in LAN (§6-§8).

### Algoritmo (identico su PC e PWA)

```
1. lista i file state-*.json in appDataFolder
2. per ogni file di un ALTRO device:
     se modifiedTime == cursore locale per quel file → salta
     altrimenti scarica e applica come snapshot (merge LWW, §3-§4);
     aggiorna il cursore (meta drive_seen)
3. ricostruisci il PROPRIO stato (che ora include la fusione appena fatta)
   e caricalo (create o update del proprio file);
   se l'impronta del contenuto (soli record, esclusi ts/diary_lines) è uguale
   all'ultimo upload e il file esiste già → non ricaricare
```

Ogni device scrive SOLO il proprio file → niente collisioni tra sync
simultanee (problema #10 del PIANO-V2). Un file con `schema` diverso da 1
viene saltato e loggato: mai corrompere.

### OAuth

- **PC**: authorization code + PKCE (client "Desktop"); il callback torna
  sull'app (`/impostazioni/drive/callback`); refresh token in settings_store
  (DB in `app/data/`, mai nel repo). Refresh automatico; `invalid_grant`
  (accesso revocato) → token dimenticato, dati locali intatti.
- **PWA**: flusso implicit con redirect di pagina intera (client "Web", senza
  secret); token (~1h) in IndexedDB `meta`; alla scadenza si ripassa dal
  consenso al tocco successivo. Niente popup (inaffidabili nelle PWA
  standalone iOS) e niente script esterni.

Setup delle credenziali (una tantum, account dell'utente): `docs/SETUP-DRIVE.md`.
