# Routine: Report titoli — FASE 2 (analisi e sintesi) — versione efficiente

Sei l'esecutore autonomo del sistema. **Rispetta sempre `CLAUDE.md`**: mai segnali
operativi; ogni stima d'impatto con disclaimer + confidenza; cita le fonti; italiano
semplice; mai esporre la chiave API. Il sistema aiuta a CAPIRE, non prevede i prezzi.

> ## ⚠️ EFFICIENZA — vincolo di budget (NON NEGOZIABILE)
> Il budget di token è la risorsa più scarsa. Quindi:
> 1. **UNA sola WebSearch per titolo.** Niente query multiple sullo stesso titolo.
> 2. **NON aprire/scaricare gli articoli** (niente fetch). Lavora sugli **snippet**
>    dei risultati di ricerca. Apri un articolo **solo** se è indispensabile per
>    riassumere correttamente una notizia **già sopra soglia** (caso raro).
> 3. **Triage prima, analisi dopo**: l'analisi completa va fatta SOLO sulle poche
>    notizie che superano la soglia. Sui titoli senza notizie rilevanti non
>    ragionare e non scrivere nulla: passa oltre.
> 4. Sii **conciso** in ogni passo. Non rileggere file inutilmente.

## Passo 1 — Carica configurazione e stato
Leggi `config/settings.yaml`, `config/portfolio.yaml`, `state/seen.json`,
`state/predictions.json`. Una lettura ciascuno.

## Passo 2 — TRIAGE (fase economica, solo snippet)
Per ogni titolo del portfolio:
- fai **una** WebSearch per notizie delle ultime ~36 ore (nome + ticker; per gli
  **ETF** cerca il tema/flussi/ribilanciamenti, non earnings);
- guarda **solo gli snippet**;
- scarta subito ciò che è già in `seen.json`, il rumore e l'off-topic;
- per ciò che resta, stima **al volo** la rilevanza (vedi rubrica) e tieni solo i
  candidati con rilevanza >= soglia del titolo (altrimenti `soglia_rilevanza_globale`).
Se un titolo non ha candidati, **passa oltre senza scrivere nulla**.
Tieni una lista breve dei candidati sopravvissuti (titolo, ticker, fonte, punteggio).

## Passo 3 — ANALISI (solo sui candidati sopra soglia)
Solo per i candidati sopravvissuti, e aggregando in **una voce** la stessa notizia
da più fonti, compila:
- `tipo_evento` (tassonomia sotto)
- `riassunto`: 2-3 frasi in italiano semplice
- `fonti`: una o più (testata + link)
- `impatto`: `{ breve, medio, lungo }` ∈ `{positivo, negativo, neutro}`
- `confidenza`: `bassa | media | alta`
- `tag`: tematici
- `sentiment_analisti` (solo **se già presente** negli snippet): rating/target/revisioni
- `rilevanza`: 0-100
Se una notizia tocca **più titoli**, segnalalo nella voce (una voce sola).
Ricorda: l'impatto è **analisi qualitativa**, non una previsione, mai un consiglio.

### Tassonomia `tipo_evento`
- **Azioni**: earnings · upgrade/downgrade analisti · revisione guidance · M&A ·
  cambio CEO/management · dividendi/buyback · legale/regolatorio · prodotto ·
  news aziendale · macro.
- **ETF**: flussi · ribilanciamento/cambio indice · composizione · costi (TER) ·
  distribuzioni · macro tematica.

### Rubrica `rilevanza` (0-100)
tipo evento × magnitudo/sorpresa × recenza × quanto tocca direttamente il titolo ×
`peso`/`priorita` del titolo. Bande: 80-100 critico · 60-79 importante ·
40-59 da report · <40 rumore (scarta).

## Passo 4 — Decidi se inviare
- Ordina i candidati per `rilevanza` decrescente.
- `test_mode: true` → invia sempre (oggetto con `[PROVA]`); se nessun candidato,
  manda un'email di prova diagnostica breve (titoli cercati, candidati, soglia).
- `test_mode: false` e nessun candidato >= soglia → **NON inviare**. Vai al Passo 6.

## Passo 5 — Costruisci e invia l'email (HTML responsive — mobile first)
Mantieni lo stile attuale (palette navy `#1a2b4a` / grigi, pulito). Requisiti:
- `<meta name="viewport" content="width=device-width, initial-scale=1">`.
- Contenitore esterno **fluido**: `width:100%; max-width:600px;` centrato. **Niente
  larghezze fisse in px** sui contenuti; font >= 14px.
- Struttura: intestazione con data → **Da leggere oggi** (le 3-5 voci a rilevanza
  più alta, una riga ciascuna) → card per notizia → footer con **disclaimer**.
- **Impatto e confidenza come "pillole" che vanno a capo da sole** (NON una riga
  larga unica, che su mobile si taglia). Ogni pillola:
  `display:inline-block; padding:4px 8px; border-radius:12px; margin:2px 4px 2px 0;
  font-size:13px; white-space:nowrap;`. Quattro pillole separate:
  `Breve ▲` · `Medio =` · `Lungo ▼` · `Confidenza: media`
  (▲ verde positivo, = grigio neutro, ▼ rosso negativo). Le pillole, essendo
  inline-block, si dispongono su più righe sugli schermi stretti senza tagliarsi.
- Card a larghezza fluida (`width:100%`), non in tabelle a larghezza fissa.
Salva l'HTML in `out.html` e invia (la chiave è in variabile d'ambiente):
```bash
python scripts/send_email.py --to "<destinatario>" --from "<mittente>" \
  --subject "📊 Monitor titoli — <data>" --html-file out.html
```
Se lo script esce != 0: invio fallito → non aggiornare `seen.json`, logga l'errore.

## Passo 6 — Aggiorna stato, logga le stime, committa su `main`
- `seen.json`: voci inviate (`id`, `ticker`, `url`, `data_invio`).
- `predictions.json`: per ogni voce inviata `{id, ticker, data, tipo_evento,
  impatto:{breve,medio,lungo}, confidenza, rilevanza, titolo, url}`.
- `runlog.ndjson`: una riga `{ts, routine:"report", titoli_cercati, notizie_trovate,
  notizie_inviate, email_inviata, note}`.
- Committa lo stato **su `main`** (la routine lavora su un branch `claude/...`):
  ```bash
  git add state/
  git commit -m "stato: run report <data>"
  git push origin HEAD:main
  ```

## Robustezza
- Errori isolati (una ricerca/fonte) → logga e prosegui, non fermare la run.
- Non stampare mai `RESEND_API_KEY`.
