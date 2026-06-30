# Contesto progetto — briefing per una nuova chat

> Incolla o allega questo file all'inizio di una chat nuova per dare tutto il
> contesto. È scritto per un assistente (Claude) che riparte da zero.
> Ultimo aggiornamento: **2026-06-30**.

---

## 0. Chi sono e come voglio lavorare

- Utente: **Lorenzo Dainelli**, italiano, piano **Claude Pro**. **Rispondimi in italiano.**
- Metodo (importante): **discutere prima, costruire a fasi**, partire dal pezzo più
  semplice e funzionante, e **dopo ogni fase fermarsi e farmi provare** prima di andare
  avanti. Onestà intellettuale sui limiti: verifica sui fatti, non andare a memoria.
- Repo unico (monorepo) su GitHub **privato**: `github.com/LorenzoDainelli/news-monitor`.
- Cartella di lavoro locale: `C:\Users\loren\Desktop\Claude\Report` (Windows 11, PowerShell).

Nel repo convivono **DUE sistemi distinti** che condividono lo stesso repo:

1. **news-monitor** — robot che gira nel **cloud** (Routines di Claude Code) e mi manda
   email coi titoli da seguire. NON si tocca mai senza motivo: è in produzione.
2. **app finanza personale** — app **locale** nella cartella `app/`, che giro sul mio PC.
   È qui che stiamo costruendo le fasi.

---

## 1. Regole NON NEGOZIABILI (valgono per entrambi)

- **Mai segnali operativi**: mai "compra/vendi/entra/esci". Lo strumento aiuta a CAPIRE,
  non dice cosa fare. La decisione è sempre mia.
- **Non è un oracolo**: non prevede i prezzi. Ogni stima d'impatto ha **disclaimer** +
  **livello di confidenza dichiarato (bassa/media/alta)**.
- **Cita sempre le fonti** (testata + link) per ogni notizia.
- **Italiano semplice**, riassunti di 2-3 frasi leggibili da telefono.
- **Mai esporre segreti**: chiavi/token (`RESEND_API_KEY`, `FINNHUB_API_KEY`, chiave
  Gemini) mai stampati, loggati o committati.
- **Privacy app (filtro per sezione)**: a Gemini **mai** ISIN/importi/valore/quantità
  (portafoglio), **mai** carte/IBAN/nome (finanze), **mai** il mio nome. I dati personali
  e le chiavi stanno **solo** in `app/data/` (gitignored, mai online).

Queste regole sono anche in `CLAUDE.md` (caricato automaticamente nel cloud).

---

## 2. Parte A — news-monitor (cloud, in produzione)

Monitora un portfolio reale (**~38 titoli**: 11 ETF + 27 azioni, mercati di tutto il
mondo; io sono in Italia/CET) e manda **email** (HTML navy/grigio, PDF per i report
pesanti). Orchestrato da **Routines di Claude Code** (girano solo su modelli Claude:
Haiku/Sonnet/Opus — **non** si può usare Gemini per le routine).

**Architettura "anti-costo"**: il modello emette solo JSON di analisi; gli **script**
fanno il lavoro meccanico:
- `scripts/fetch_news.py` — scarica le news (API **Finnhub**) e passa al modello un
  digest compatto. Gestisce la dedup a monte (`--seen-file`).
- `scripts/render_email.py` — costruisce l'HTML dal JSON.
- `scripts/update_state.py` — aggiorna lo stato (dedup + pruning 30 giorni).
- `scripts/send_email.py` — invio via **Resend** (serve User-Agent "browser" o
  Cloudflare blocca con errore 1010).
- `scripts/newskey.py` — `news_key(url)`: chiave di dedup deterministica dall'URL.
- Stato in `state/` (es. `state/seen.json`, `state/predictions.json`), committato su `main`.

**Routine attive** (Report, Event-check, Settimanale, Mensile). Tetto Pro = 5 run/giorno;
nei feriali sono esattamente 5. L'Event-check **invia SEMPRE** un'email: 🚨 se c'è
qualcosa di critico, altrimenti ✅ "tutto tranquillo".

**Soglie attuali** (abbassate su mia richiesta): rilevanza report **50**, evento critico
**70** (`config/settings.yaml`: `soglia_rilevanza_globale: 50`, `soglia_evento_critico: 70`,
`max_notizie_email: 10`).

### ⚠️ Learning importante — i CRON delle routine sono in UTC
Il cron **personalizzato** (digitato a mano, più orari con la virgola) viene eseguito in
**UTC**; la UI mostra solo il numero grezzo senza convertire il fuso → inganna. I **preset**
(un solo orario scelto dal menu) convertono da soli local→UTC. Prova decisiva: cron `0 7`
→ email arrivata alle **09:00 italiane** (= 07:00 UTC).
Valori corretti (estate CEST = UTC+2 → `cron = ora_locale − 2`):
- Report: `0 5,17 * * 1-5` (arriva 07:00/19:00 IT)
- Event-check: `0 9,13,20 * * 1-5` (arriva 11:00/15:00/22:00 IT)
- In inverno (CET = UTC+1) aggiungere 1h.

### ⚠️ Learning importante — dedup per URL **e** per evento
Bug grave risolto: la stessa notizia usciva più volte con punteggi opposti. Causa: dedup
sul campo `id` che il modello inventa diverso ogni volta, e `seen.json` non salvava il
titolo. Fix: dedup per **URL normalizzato** (`newskey.py`) **e** per **evento** (stesso
fatto da fonte/URL diversa = non reinviare, via `recent_seen`). Aggiunta regola di
"valutazione equilibrata" per le notizie a doppia faccia (impatto netto + trade-off).

---

## 3. Parte B — app finanza personale (locale) — **è qui che lavoriamo**

App **locale e gratuita** che unisce **portafoglio investimenti**, **finanze personali**
(entrate/uscite, saldi) e un **agente AI**. Vive in `app/` nello stesso repo così può
leggere le notizie del robot e riusare la lista titoli.

### Stack
- **FastAPI + Jinja2 + SQLAlchemy/SQLite**. Python 3.11. Server solo su `127.0.0.1`.
- DB locale: `app/data/finanza.db` (gitignored). Chiavi API in tabella `shared_settings`.
- Si avvia col **doppio click su `Avvia-Finanza.bat`** (apre il browser).
- ⚠️ `run.py` usa `reload=False` → **dopo ogni modifica al codice devo RIAVVIARE l'app**
  (chiudere la finestra nera e riaprire il .bat). Non si ricarica da sola.
- Base valuta **EUR**. UI **tema chiaro/scuro** + **multilingua 6 lingue** (IT/EN/ES/FR/DE/UK).

### Dove vivono le cose (mappa)
- **Pagine HTML** → `app/templates/` (`base.html` è lo scheletro comune da cui ereditano).
- **Aspetto (colori/font/spaziature, tema)** → `app/static/style.css` (tutto a variabili CSS).
- **Animazioni portafogli** (scene canvas) → `app/static/wallet-board.js` + `.css`.
- **Traduzioni 6 lingue** → `app/shared/i18n.py` (gli HTML usano `t('chiave')`).
- **Logica**: `app/portfolio/`, `app/finance/`, `app/news/`, `app/shared/`.

### Le FASI (roadmap logica) — stato
- **Fase 0** ✅ scheletro app
- **Fase 1** ✅ portafoglio offline (CRUD + PAC)
- **Fase 1.5** ✅ fondamenta UX: tema chiaro/scuro + multilingua 6 lingue + aggancio login
- **Fase 2** ✅ prezzi live (Yahoo/Stooq, EUR), holdings ETF, pagina `/analisi`
  (look-through settoriale, concentrazione, dividend yield, rischio vol/drawdown/Sharpe/beta)
- **Fase 3** ✅ finanze personali: wallet con saldo, movimenti entrata/uscita/trasferimento,
  categorie riusate/unite, 4 wallet precaricati
- **Fase UX 2** ✅ (passi 1-3) board "treemap" dei portafogli (tessere grandi quanto pesano,
  squarified) con scene canvas vive **senza dipendenze (offline)**: Contanti = montagna di
  banconote + fuoco, Conto = caveau, PAC = pianta, Carta = carta + onde. Stile scelto:
  **ESUBERANTE**; principio chiave **animazioni SOLO durante l'evento** (a riposo quadro
  fermo, esplode 2-3s e si calma). Anteprima ＋/− su ogni tessera + **autoplay sul movimento
  reale** (redirect `?play=<id>&dir=in|out`). Interruttore **Piene/Leggere/Spente** in
  Impostazioni (pref `ui_anim`, rispetta `prefers-reduced-motion`). Scena Contanti già
  arricchita: **mazzette** che cadono + **fuoco a lingue multicolore**, banconota che brucia
  piano. **Da fare:** portare Conto/Carta/PAC allo stesso livello; poi font/pulsanti/spaziature.
- **Fase 5** ✅ sezione **Notizie** (`/notizie`): legge `state/predictions.json` del robot e
  mostra le card stile email (impatto breve/medio/lungo, rilevanza, confidenza, fonte). Sola lettura.
- **Fase 4** ✅ **COMPLETATA in questa chat** (agente AI) — vedi sotto.

### RESTANTI / prossimi passi
- **Rifiniture UX**: arricchire le scene Conto/Carta/PAC come Contanti; poi "fondamenta"
  tipografia/pulsanti/spaziature su tutto il sito. (Sono lavori **visivi**: l'assistente
  non vede i pixel → meglio che li indirizzi io, o che li verifichi io dal sito.)
- Possibile arricchimento Notizie (far emettere al robot un file con riassunto/fonti).
- Idea futura: **versamenti mensili** (ponte PAC↔finanze), con l'AI che impara gli andamenti.

---

## 4. Cosa abbiamo fatto in QUESTA chat (2026-06-30)

### Fase 4 completata — agente AI
La chiave Gemini la metto io in **Impostazioni**; tutto il resto è pronto. Senza chiave
le funzioni AI degradano con grazia (invito a Impostazioni), niente errori.

1. **Filtro privacy** (`app/shared/privacy.py`): `scrub_text()` oscura IBAN/ISIN/numeri di
   carta (13-19 cifre)/nome prima di inviare all'AI. Gli importi piccoli restano (servono
   al parsing, non sono sensibili).
2. **Spese in linguaggio naturale**: scrivo es. *"ieri 20€ di benzina con la carta"* nel
   box ✨ in *Finanze*/*Movimenti* → l'AI (`ai.parse_movimento`) **precompila il modulo**
   (tipo/importo/categoria/portafoglio/data) e **io controllo e salvo**. Nessun salvataggio
   automatico. Rotta `POST /finanze/ai/parse`.
3. **Analisi descrittiva del mese** (`ai.analizza_finanze`): card in panoramica, su un
   riassunto **aggregato e anonimo** (ultimi 3 mesi, solo totali + categorie). Solo fatti,
   con confidenza e disclaimer. Rotta `POST /finanze/ai/analisi`.
4. i18n 6 lingue per tutte le nuove etichette.

### Scoperta + bugfix sull'agente
- Nel DB c'era **già una chiave Gemini valida** (l'agente era di fatto già sbloccato).
- Ma il **modello salvato era `gemini-1.5-flash`** → **404** (i modelli 1.5 sono stati
  ritirati nel 2026). Risolto: impostazione corretta a **`gemini-2.0-flash`** + aggiunto in
  `ai._call` un **ripiego automatico sul default se un modello dà 404** (auto-riparazione).
- Le chiamate di test hanno poi dato **429** = limite di richieste del free tier (è solo il
  rate limit del minuto per le troppe prove ravvicinate; si resetta da solo).

### Rifiniture + pulizia codice (revisione anomalie)
- **Bug reale risolto**: dopo il parse AI, il modulo aveva `next` = `/finanze/ai/parse`
  (una rotta senza GET) → al salvataggio avrebbe dato 405. Fix con `next_url` esplicito.
- Importo precompilato dall'AI ora mostrato all'**italiana** ("20,00").
- Rimossa una chiave i18n morta (`fin.ai_note`).
- **Feedback "Prova connessione"** ora specifico: distingue chiave errata / **429 rate
  limit** / rete / altro, invece del generico "errore".
- Stile dedicato per gli elementi dell'agente (`.ai-box`, `.ai-out`) con variabile `--ai`
  viola, tema-consapevole (chiaro/scuro).
- Controlli automatici passati: compilazione di tutti i `.py`; checker chiavi i18n (nessuna
  mancante); checker import inutili (nessuno); render delle pagine finanze in `HTTP 200`.

---

## 4-bis. Chat grafica esuberante + chiave Gemini (2026-06-30, sessione successiva)

### Decisioni di design (discusse e approvate)
- Confronto a 3 stili (sobrio / "terza via" / esuberante) via mockup. **Scelto: ESUBERANTE.**
- L'utente vuole, per i Contanti: **mazzette di banconote verdi che cascano** con fisica e
  atterrano su una **montagna di banconote**; **fuoco di vari colori come un fuoco vero**;
  le **banconote spese che bruciano pian piano** (intensità ∝ quanto si spende). Per le
  dimensioni: una **scatola/treemap** dove i portafogli sono quadrati/semi-quadrati di
  grandezza diversa che **si ridimensionano** in base al % del patrimonio.
- Principio non negoziabile concordato: **animazioni solo durante l'evento** (a riposo
  fermo) per restare leggere e gratis; interruttore **Piene/Leggere/Spente**; ogni tipo di
  portafoglio con la **sua** scena viva.
- Costo: **0 €**, tutto canvas a mano, nessuna libreria, funziona offline.

### Cosa è stato costruito (commit `ffd99f6`, `35d5721`, `b0093d4`, tutti su main)
- `app/static/wallet-board.js` + `wallet-board.css`: treemap squarified (valori ordinati
  desc → tessere quadrate), scene per tipo, fisica leggera, fuoco multicolore (`drawFlames`),
  banconota che brucia. Board in **/finanze** (panoramica) e **/finanze/portafogli**.
- Autoplay sul movimento reale: `app/finance/routes.py` fa redirect `?play=&dir=`,
  il board legge il parametro e fa partire la scena (trasferimento escluso).
- Guardia se non ci sono portafogli (niente box vuoto). Blocchi `head`/`scripts` in `base.html`.

### Chiave Gemini — guida (problema reale dell'utente)
- Serve la chiave **gratuita** di Google AI Studio: deve iniziare con **`AIza…`**, creata sul
  progetto **"Default Gemini Project"**, **senza collegare carta/fatturazione**.
- Una chiave che inizia con **`AQ.Ab`** o che chiede un metodo di pagamento = ramo
  **a pagamento / Cloud (Vertex)**, **non compatibile** con l'endpoint gratuito → dà errore
  subito a "Prova connessione".
- Sul **piano gratuito non si può essere addebitati**: oltre il limite arriva solo un errore
  temporaneo **429**, mai un costo. L'app fa pochissime chiamate ("a domanda") → limiti mai sfiorati.
- Se si tiene una chiave col billing, mettere un **budget/quota a 0** in Google Cloud per sicurezza.

### Preferenze emerse in questa chat
- **Niente preview/screenshot**: scrivere/aggiornare il codice, l'utente **controlla dal sito**.
- L'utente ha **cancellato per sbaglio il wallet "Contanti"**: va bene, si ricrea da *Gestisci
  portafogli* (tipo "Contanti") e la scena montagna+fuoco torna.

---

## 5. Stato attuale e cose che spettano a me (utente)

- ▶️ **Riavviare l'app** per caricare il nuovo codice (chiudere la finestra nera, riaprire
  `Avvia-Finanza.bat`).
- ▶️ In **Impostazioni → Agente AI → "Prova connessione"**: se dà OK l'agente è pronto; se
  dà 429 riprovare tra un minuto.
- ▶️ Provare il box: es. *"oggi 12€ di spesa al supermercato"* → il modulo si compila, io salvo.
- ▶️ Sul robot (cloud), lato mio: verificare/impostare i cron in **UTC** come sopra.
- ✅ **Push su GitHub FATTO**: `main` è a **`f8b9b4a`** e coincide con `origin/main`
  (Fase 4 completo + Fase 5 Notizie + grafica esuberante passi 1-3: tutto su GitHub).
  ⚠️ Esiste un branch di lavoro `claude/bold-lederberg-240199` fermo a `b0093d4`, più
  indietro di main: **una nuova chat deve lavorare su `main`**, non su quel branch.

---

## 6. Come avviare l'app (locale)
1. Doppio click su `Avvia-Finanza.bat` nella cartella del progetto.
2. Si apre il browser su `127.0.0.1`. Menu in alto: Dashboard, Portafoglio, PAC, Analisi,
   Finanze, Notizie, Impostazioni.
3. Dopo ogni modifica al codice: **chiudere e riaprire** (no auto-reload).

---

## 7. Promemoria per l'assistente che riparte
- Rispondi in **italiano**, semplice.
- **Non toccare il news-monitor** senza motivo (è in produzione).
- Le chiavi/segreti **non si stampano mai**; i dati in `app/data/` non vanno su GitHub.
- Lavora **a fasi**, fermati e fammi provare.
- I lavori **visivi** (CSS/scene canvas) non sono verificabili a occhio dall'assistente:
  proporli con prudenza e farmeli verificare dal sito.
- Dopo modifiche al codice dell'app, ricorda di dirmi di **riavviare** (`reload=False`).
