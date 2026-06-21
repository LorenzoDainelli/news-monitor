# Routine: Report titoli — FASE 1

Sei l'esecutore autonomo del sistema di monitoraggio. **Rispetta sempre le regole
in `CLAUDE.md`** (mai segnali operativi; ogni stima con disclaimer + livello di
confidenza; cita le fonti; italiano semplice; mai esporre la chiave API).
Esegui i passi nell'ordine.

## Passo 1 — Carica configurazione e stato
- Leggi `config/settings.yaml` e `config/portfolio.yaml`.
- Leggi `state/seen.json` (notizie già inviate in passato).

## Passo 2 — Cerca le notizie
Per ogni titolo in `portfolio.yaml`, usa lo strumento **WebSearch** per trovare
notizie delle ultime ~36 ore. Costruisci query con nome azienda + ticker (es.
`Apple AAPL news`). Privilegia fonti affidabili (Reuters, Bloomberg, FT, WSJ,
CNBC, Il Sole 24 Ore). Se una ricerca non risponde, logga e prosegui con il resto.

## Passo 3 — Filtra, deduplica, riassumi
- **Dedup**: scarta le notizie il cui identificativo è già in `state/seen.json`
  (usa l'URL normalizzato; in mancanza, il titolo).
- Per ogni notizia restante: riassunto di **2-3 frasi in italiano** + fonte
  (testata + link).
- Assegna un **punteggio di rilevanza 0-100**. Tieni solo le notizie con punteggio
  >= soglia del titolo (`soglia_rilevanza` in portfolio.yaml; in mancanza,
  `soglia_rilevanza_globale` in settings.yaml).

## Passo 4 — Decidi se inviare
- Se `test_mode: true`:
  - se ci sono notizie sopra soglia → invia il report normale, ma con `[PROVA]`
    nell'oggetto;
  - se NON ci sono notizie sopra soglia → invia comunque un'**email di prova**
    diagnostica che dice chiaramente "EMAIL DI PROVA — sistema attivo" e riporta:
    titolo cercato, n. risultati trovati, soglia applicata. Serve a validare
    l'invio end-to-end.
- Se `test_mode: false`:
  - se nessuna notizia >= soglia → **NON inviare email**. Salta al Passo 6.
  - altrimenti → invia il report.

## Passo 5 — Costruisci e invia l'email
- Genera HTML pulito e responsive (palette navy `#1a2b4a` / grigi, leggibile da
  telefono). Struttura: intestazione con data; per ogni titolo, le voci notizia
  (riassunto, fonte con link, punteggio); footer con **disclaimer** (analisi
  qualitativa, nessuna previsione di prezzo, nessun segnale operativo).
- Salva l'HTML in `out.html`.
- Invia con lo script (la chiave sta nella variabile d'ambiente, non passarla):
  ```bash
  python scripts/send_email.py \
    --to "<destinatario da settings.yaml>" \
    --from "<mittente da settings.yaml>" \
    --subject "📊 Monitor titoli — <data odierna>" \
    --html-file out.html
  ```
- Se lo script esce con codice != 0, l'invio è fallito: **non** aggiornare
  `seen.json` (così la notizia verrà ritentata), e logga l'errore al Passo 6.

## Passo 6 — Aggiorna stato e committa
- Se l'email è stata inviata con successo, aggiungi a `state/seen.json` le notizie
  effettivamente inviate (campi: `id`, `ticker`, `url`, `data_invio`).
- Aggiungi **sempre** una riga a `state/runlog.ndjson` (JSON su singola riga):
  `{"ts": "<ISO 8601>", "routine": "report", "titoli_cercati": N,
  "notizie_trovate": N, "notizie_inviate": N, "email_inviata": true/false,
  "note": "..."}`.
- Committa lo stato:
  ```bash
  git add state/ && git commit -m "stato: run report <data>" && git push
  ```
  (Richiede l'opzione **Allow unrestricted branch pushes** abilitata sul repo,
  così il commit arriva su `main` e viene riletto alla run successiva.)

## Note di robustezza
- Errori isolati (una ricerca, una fonte) → logga e prosegui, non fermare la run.
- Non stampare mai `RESEND_API_KEY`.
- Mantieni i passi efficienti per non sprecare budget.
