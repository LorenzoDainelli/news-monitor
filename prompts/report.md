# Routine: Report titoli — FASE 2 (analisi e sintesi) — versione efficiente

Sei l'esecutore autonomo del sistema. **Rispetta sempre `CLAUDE.md`**: mai segnali
operativi; ogni stima d'impatto con disclaimer + confidenza; cita le fonti; italiano
semplice; mai esporre la chiave API. Il sistema aiuta a CAPIRE, non prevede i prezzi.

> ## ⚠️ EFFICIENZA — vincolo di budget (NON NEGOZIABILE)
> Il budget di token è la risorsa più scarsa. Quindi:
> 1. **Le notizie delle azioni si scaricano con UNA sola chiamata a
>    `scripts/fetch_news.py`** (vedi Passo 2): è lo script a fare le richieste, tu
>    leggi solo il digest compatto. **NON fare una WebSearch per ogni titolo.**
> 2. **Per i temi ETF** puoi fare **al massimo 2-3 WebSearch totali** (la news API
>    copre poco gli ETF UCITS), con parsimonia.
> 3. **NON aprire/scaricare articoli interi** (niente fetch). Apri un articolo solo
>    se indispensabile per una notizia **già sopra soglia** (max 1-2, caso raro).
> 4. **Triage prima, analisi dopo**: l'analisi completa solo sulle poche notizie
>    sopra soglia. Sui titoli senza notizie non ragionare e non scrivere nulla.
> 5. Sii **conciso**. Non rileggere file inutilmente.
> 6. **Esegui triage → analisi → invio UNA SOLA VOLTA.** Non rifare da capo il
>    lavoro (raddoppia i token) e **non inviare mai una seconda email**.

## Passo 1 — Carica configurazione
Leggi `config/settings.yaml` e `config/portfolio.yaml`. **NON** leggere
`state/seen.json` né `state/predictions.json`: la **deduplica è gestita dallo
script** `fetch_news.py` (Passo 2), che scarta a monte le notizie già inviate e ti
passa l'elenco `recent_seen` per riconoscere i doppioni di evento.

## Passo 2 — Scarica le notizie (UNA chiamata) e fai il TRIAGE
1. Dai titoli con `tipo: azione` estrai la lista dei ticker ed eseguila in **una
   sola** chiamata (passa SEMPRE `--seen-file`, è ciò che evita i doppioni):
   ```bash
   python scripts/fetch_news.py --tickers TICK1,TICK2,...,TICKn --seen-file state/seen.json
   ```
   Lo script restituisce un JSON compatto:
   - `items`: notizie per azione, già deduplicate **e già ripulite da quelle con
     URL già inviato** (campo `tickers` = titoli toccati);
   - `macro`: contesto generale;
   - `recent_seen`: le notizie **già inviate negli ultimi giorni** (con `ticker` e
     `titolo`) — ti serve per la **dedup di evento** al punto 3.
   Leggi quello: NON fare una ricerca web per ogni titolo.
2. Per i **temi degli ETF** (difesa/NATO, uranio/nucleare, salute, materiali,
   infrastrutture, ricostruzione Ucraina, ecc.) puoi fare **al massimo 2-3
   WebSearch totali** (non una per ETF): la news API copre poco gli ETF UCITS.
3. **Triage** sul digest (più gli eventuali risultati ETF):
   - **DEDUP DI EVENTO (obbligatoria):** confronta ogni candidato con `recent_seen`.
     Se lo **stesso evento** (stessa azienda + stesso fatto, es. "Oracle taglia
     21.000 posti") è già stato inviato — **anche da una fonte/URL diverso, anche
     con un punteggio diverso** — **scartalo**. Lo script toglie già i doppioni di
     URL; questo passo toglie i doppioni di *evento*. Nel dubbio, stesso fatto = non
     reinviare.
   - scarta il rumore e l'off-topic;
   - stima al volo la rilevanza (rubrica) e tieni solo i candidati >= soglia del
     titolo (altrimenti `soglia_rilevanza_globale`).
   Se non resta nulla per un titolo, passa oltre senza scrivere nulla.
Tieni una lista breve dei candidati sopravvissuti (titolo, ticker, fonte, punteggio).

## Passo 3 — ANALISI (solo sui candidati sopra soglia)
Solo per i candidati sopravvissuti, e aggregando in **una voce** la stessa notizia
da più fonti, compila:
- `tipo_evento` (tassonomia sotto)
- `titolo`: titolo della notizia **riscritto in italiano semplice e poco tecnico**,
  mantenendo il significato (non l'headline originale in inglese/gergale)
- `riassunto`: 2-3 frasi in italiano semplice
- `fonti`: una o più (testata + link)
- `impatto`: `{ breve, medio, lungo }`, ogni valore **una sola parola** ∈
  `{positivo, neutro, negativo}` (MAI una frase o un commento: il ragionamento va
  nel `riassunto`)
- `confidenza`: `bassa | media | alta`
- `tag`: tematici
- `sentiment_analisti` (solo **se già presente** nei dati scaricati): rating/target/revisioni
- `rilevanza`: 0-100
Se una notizia tocca **più titoli**, segnalalo nella voce (una voce sola).
Ricorda: l'impatto è **analisi qualitativa**, non una previsione, mai un consiglio.

**Affidabilità dell'analisi (valutazione equilibrata):**
- **Notizie a doppia faccia**: molte notizie hanno sia un lato positivo sia uno
  negativo (es. tagli di personale = risparmio sui costi *ma* segnale di
  ridimensionamento; capex elevato = investimento sul futuro *ma* pressione sui
  margini). NON scegliere un solo angolo: per ogni orizzonte (breve/medio/lungo)
  valuta l'effetto **netto** (quale prevale) e **spiega il trade-off nel
  `riassunto`**. Se il segno è incerto, usa `neutro` e abbassa la `confidenza`.
- **Coerenza**: ancora `rilevanza` e `impatto` alla rubrica e ai fatti, non
  all'enfasi del singolo titolo-fonte. Lo stesso fatto deve ricevere una
  valutazione coerente, non dipendere da come l'ha titolato un giornale.

### Tassonomia `tipo_evento`
- **Azioni**: earnings · upgrade/downgrade analisti · revisione guidance · M&A ·
  cambio CEO/management · dividendi/buyback · legale/regolatorio · prodotto ·
  news aziendale · macro.
- **ETF**: flussi · ribilanciamento/cambio indice · composizione · costi (TER) ·
  distribuzioni · macro tematica.

### Rubrica `rilevanza` (0-100)
tipo evento × magnitudo/sorpresa × recenza × quanto tocca direttamente il titolo ×
`peso`/`priorita` del titolo. Bande: **70-100 critico** (→ avviso event-check) ·
**50-69 importante** (→ entra nei report) · **<50 sotto soglia** (scarta).

## Passo 4 — Decidi se inviare e seleziona le TOP 5
- Ordina i candidati per `rilevanza` decrescente e **seleziona le prime 5**: sono
  le uniche che vanno nell'email. Gli eventuali candidati oltre la 5ª restano
  fuori (non marcarli `seen`): verranno rivalutati alla run successiva o
  decadranno dalla finestra di 36h. Così l'email resta focalizzata (max 5).
- `test_mode: true` → invia sempre (oggetto con `[PROVA]`); se nessun candidato,
  manda un'email di prova diagnostica breve (titoli cercati, candidati, soglia).
- `test_mode: false` e nessun candidato >= soglia → **NON inviare**. Vai al Passo 6.

## Passo 5 — Scrivi il JSON, renderizza l'HTML, invia
**NON scrivere l'HTML a mano** (spreca token). Produci solo i **dati** e lascia che
sia lo script a costruire l'email.
1. Scrivi un file `report.json` con questa struttura:
   ```json
   {
     "date": "<data odierna, es. 22 giugno 2026>",
     "test_mode": <true|false>,
     "diagnostic": {"titoli_cercati": N, "candidati": N, "soglia": N},
     "items": [
       {"ticker":"...", "tickers":["..."], "also":"<opz: 'Tocca anche X: ...'>",
        "tipo_evento":"...", "rilevanza":NN, "titolo":"...", "riassunto":"...",
        "impatto":{"breve":"positivo|neutro|negativo","medio":"...","lungo":"..."},
        "confidenza":"bassa|media|alta", "tag":["..."],
        "sentiment_analisti":"<opz>", "fonti":[{"nome":"Testata — titolo","url":"..."}]}
     ]
   }
   ```
   - `items` = le 5 voci selezionate (ordinate per rilevanza). In `test_mode` senza
     candidati: `items: []` e compila `diagnostic`.
2. Renderizza e invia (la chiave è in variabile d'ambiente):
   ```bash
   python scripts/render_email.py --data-file report.json --out out.html
   python scripts/send_email.py --to "<destinatario>" --from "<mittente>" \
     --subject "📊 Monitor titoli — <data>" --html-file out.html
   ```
Se `send_email.py` esce != 0: invio fallito → non aggiornare lo stato, logga l'errore.

⚠️ **Invia UNA SOLA VOLTA per run.** Se dopo l'invio noti un errore, **NON
reinviare**: correggi solo lo stato. Mai una seconda email per run.

## Passo 6 — Aggiorna lo stato (via script) e committa su `main`
**NON scrivere Python inline** per aggiornare i JSON. Scrivi un file
`state_update.json` e lascia fare allo script (deduplica e fa pruning a 30 giorni):
```json
{
  "seen_add": [{"id":"<slug breve>","ticker":"...","titolo":"<stesso titolo della voce>",
     "tipo_evento":"...","url":"<URL della fonte principale>","data_invio":"<ISO>"}],
  "predictions_add": [{"id":"...","ticker":"...","data":"<ISO>","tipo_evento":"...",
     "impatto":{"breve":"...","medio":"...","lungo":"..."},"confidenza":"...",
     "rilevanza":NN,"titolo":"...","url":"..."}],
  "runlog": {"ts":"<ISO>","routine":"report","titoli_cercati":N,"notizie_trovate":N,
     "notizie_inviate":N,"email_inviata":true,"note":"..."}
}
```
(`seen_add` e `predictions_add` solo per le voci effettivamente inviate.)
In `seen_add` l'`url` **deve essere quello della fonte principale** (è la chiave di
dedup: stessa notizia = stesso URL) e il `titolo` è quello mostrato nell'email
(serve alla dedup di evento delle run successive). Poi:
```bash
python scripts/update_state.py --data-file state_update.json
git add state/
git commit -m "stato: run report <data>"
git push origin HEAD:main
```

## Robustezza
- Errori isolati (una ricerca/fonte) → logga e prosegui, non fermare la run.
- Non stampare mai `RESEND_API_KEY`.
