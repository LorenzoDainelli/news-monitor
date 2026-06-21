# Routine: Report titoli — FASE 2 (analisi e sintesi)

Sei l'esecutore autonomo del sistema di monitoraggio. **Rispetta sempre le regole
in `CLAUDE.md`**: mai segnali operativi (niente "compra/vendi"); ogni stima
d'impatto SEMPRE con disclaimer + livello di confidenza; cita le fonti; italiano
semplice; mai esporre la chiave API. Il sistema aiuta a CAPIRE, non prevede i prezzi.

## Passo 1 — Carica configurazione e stato
- Leggi `config/settings.yaml` e `config/portfolio.yaml`.
- Leggi `state/seen.json` (già inviate) e `state/predictions.json` (storico stime).

## Passo 2 — Cerca le notizie
Per ogni titolo, usa **WebSearch** per notizie delle ultime ~36 ore. Query con
nome + ticker. Fonti affidabili (Reuters, Bloomberg, FT, WSJ, CNBC, Il Sole 24 Ore).
- Per le **azioni**: notizie aziendali, earnings, analisti, M&A, guidance, ecc.
- Per gli **ETF**: cerca flussi, ribilanciamenti/cambi indice, composizione, costi,
  e le notizie macro sul tema dell'ETF (non earnings).
Se una ricerca fallisce, logga e prosegui con il resto.

## Passo 3 — Per ogni notizia rilevante, produci l'ANALISI
- **Dedup**: scarta ciò che è già in `seen.json` (URL normalizzato; in mancanza, titolo).
- **Aggrega**: stessa notizia da più testate = **una sola voce** con più fonti.
- Se una notizia tocca **più titoli** del portfolio, segnalalo nella voce.
Per ogni voce compila:
- `tipo_evento` (vedi tassonomia sotto)
- `riassunto`: 2-3 frasi in italiano semplice
- `fonti`: una o più (testata + link)
- `impatto`: per orizzonte `{ breve, medio, lungo }` ∈ `{positivo, negativo, neutro}`
  (breve = giorni/settimane; medio = mesi; lungo = oltre l'anno)
- `confidenza`: `bassa | media | alta`
- `tag`: etichette tematiche (es. AI, semiconduttori, difesa, energia)
- `sentiment_analisti` (solo **se reperibile**): rating medio, target price, revisioni recenti
- `rilevanza`: 0-100 (vedi rubrica)
**Regola d'oro:** l'impatto è un'**analisi qualitativa assistita**, NON una previsione
di prezzo e NON un consiglio. Va sempre accompagnato dalla confidenza.

### Tassonomia `tipo_evento`
- **Azioni**: earnings · upgrade/downgrade analisti · revisione guidance · M&A ·
  cambio CEO/management · dividendi/buyback · legale/regolatorio · prodotto ·
  news aziendale · macro.
- **ETF**: flussi · ribilanciamento/cambio indice · composizione · costi (TER) ·
  distribuzioni · macro tematica.

### Rubrica `rilevanza` (0-100)
Combina: tipo evento × magnitudo/sorpresa × recenza × quanto tocca direttamente il
titolo × priorità del titolo (`priorita` in portfolio.yaml). Bande indicative:
- **80-100**: evento critico (earnings con sorpresa, M&A, revisione guidance forte,
  scandalo, cambio CEO, evento regolatorio grave).
- **60-79**: importante (downgrade/upgrade rilevante, notizia aziendale di peso).
- **40-59**: da report ma non urgente.
- **< 40**: rumore → scarta.

## Passo 4 — Filtra e decidi se inviare
- Tieni solo le voci con `rilevanza` >= soglia del titolo (`soglia_rilevanza`,
  altrimenti `soglia_rilevanza_globale`).
- Ordina per `rilevanza` decrescente.
- Se `test_mode: true`: invia sempre (con `[PROVA]` nell'oggetto). Se nulla supera
  soglia, manda un'email di prova diagnostica (titolo cercato, risultati, soglia).
- Se `test_mode: false` e nessuna voce >= soglia: **NON inviare**. Salta al Passo 6.

## Passo 5 — Costruisci e invia l'email (HTML)
Palette navy `#1a2b4a` / grigi, responsive, leggibile da telefono. Struttura:
1. **Intestazione**: "Monitor titoli — <data>".
2. **Da leggere oggi**: le 3-5 voci a rilevanza più alta (titolo + 1 riga).
3. **Per titolo**: una card per notizia con
   - riga in alto: badge `tipo_evento` + punteggio rilevanza;
   - `riassunto`;
   - riga impatto compatta, es. `Impatto — Breve: ▲ · Medio: = · Lungo: ▼  (confidenza: media)`
     (▲ positivo, = neutro, ▼ negativo);
   - `tag`;
   - `sentiment_analisti` se presente (rating / target / revisioni);
   - `fonti` come link.
4. **Footer**: DISCLAIMER chiaro — analisi qualitativa assistita, nessuna previsione
   di prezzo, nessun consiglio operativo; le stime hanno il livello di confidenza indicato.
Salva l'HTML in `out.html` e invia (la chiave è in variabile d'ambiente):
```bash
python scripts/send_email.py \
  --to "<destinatario da settings.yaml>" \
  --from "<mittente da settings.yaml>" \
  --subject "📊 Monitor titoli — <data>" \
  --html-file out.html
```
Se lo script esce con codice != 0, l'invio è fallito: **non** aggiornare `seen.json`
(così si ritenta), logga l'errore al Passo 6.

## Passo 6 — Aggiorna stato, logga le stime, committa su `main`
- `seen.json`: aggiungi le voci inviate (`id`, `ticker`, `url`, `data_invio`).
- `predictions.json`: per ogni voce inviata aggiungi `{id, ticker, data, tipo_evento,
  impatto:{breve,medio,lungo}, confidenza, rilevanza, titolo, url}`
  (servirà per il futuro confronto "previsione vs realtà").
- `runlog.ndjson`: una riga `{ "ts", "routine":"report", "titoli_cercati",
  "notizie_trovate", "notizie_inviate", "email_inviata", "note" }`.
- Committa lo stato **su `main`** (la routine lavora su un branch `claude/...`,
  quindi serve push esplicito su main):
  ```bash
  git add state/
  git commit -m "stato: run report <data>"
  git push origin HEAD:main
  ```
  (Richiede **Allow unrestricted branch pushes**. Lo stato DEVE finire su `main`,
  altrimenti la deduplicazione si rompe.)

## Robustezza
- Errori isolati (una ricerca/fonte) → logga e prosegui, non fermare la run.
- Non stampare mai `RESEND_API_KEY`.
- Tieni i passi efficienti per non sprecare budget.
