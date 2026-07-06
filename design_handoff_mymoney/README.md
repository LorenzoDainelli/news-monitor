# Handoff: MyMoney — nuovo design applicato all'app reale

## Overview
Questo pacchetto contiene il nuovo design ad alta fedeltà dell'app **MyMoney** (finanza
personale: patrimonio, portafoglio ETF/azioni, finanze/movimenti, PAC, analisi, notizie,
impostazioni, agente AI). L'obiettivo dell'handoff è **portare questo design nell'app reale
esistente e collegarlo ai dati veri**, così che tutto funzioni e si aggiorni dinamicamente.

L'app reale è, per quanto ricostruito, un backend **Flask + Jinja2**. Il punto di forza di
questo redesign è che **non reinventa il markup**: restilizza lo *stesso vocabolario di classi*
che i template Jinja già renderizzano (`.topbar .nav .card .stat .pill .badge .btn .table-wrap
.form .note .ai-box` ecc.). Quindi nella maggior parte dei casi **non devi riscrivere le pagine**:
sostituisci il foglio di stile e allinei l'HTML dei template a queste classi.

## About the Design Files
I file in `design_reference/` sono **riferimenti di design** — una ricostruzione interattiva in
HTML/React (Babel nel browser) che mostra aspetto e comportamento voluti. **Non sono codice di
produzione da copiare così com'è.** Sono stati scritti in React solo per rendere il prototipo
cliccabile; la tua app è in Jinja2 e i dati lì sono *finti* (`design_reference/data.js.txt`).

Il lavoro da fare è: **applicare gli stili in `styles/` all'app Flask esistente e collegare i
dati veri** (dal DB / dalle API / dal contesto Jinja), non ospitare React o gli HTML di riferimento.

I file sorgente React di riferimento hanno estensione `.txt` di proposito, così non vengono
compilati per errore: sono da **leggere**, non da eseguire.

## Fidelity
**Alta fedeltà (hi-fi).** Colori, tipografia, spaziature, ombre, stati e micro-interazioni sono
definitivi. Ricrea l'UI in modo fedele usando i token e il CSS forniti — non reinventare valori.

## Cosa è pronto all'uso vs. cosa va ricreato
- **Pronto all'uso (copiare così com'è):** tutto ciò che sta in `styles/` — i token CSS e il
  foglio componenti `mymoney.css`. È già scritto per restilizzare le classi Jinja esistenti.
- **Da ricreare/collegare:** il markup dei template Jinja (deve usare esattamente queste classi),
  e soprattutto **il collegamento ai dati reali**: ogni numero, riga di tabella, movimento e
  grafico mostrato nel riferimento deve provenire dai tuoi dati veri, non dai mock.

---

## Come installarlo nell'app Flask (percorso consigliato)

1. **Copia i CSS** in `app/static/`:
   - `styles/styles.css` → il file entry: fa `@import` di tutto in ordine (fonts → token →
     `mymoney.css`). È **l'unico** file che i template devono linkare.
   - `styles/tokens/` → la cartella dei token (colori, tipografia, spaziature, raggi, ombre,
     glass, motion, scenes).
   - `styles/mymoney.css` → il foglio dei componenti (restyle delle classi Jinja).

2. **Linka un solo foglio** nel `base.html`/layout Jinja:
   ```html
   <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
   ```
   (Aggiungi i preconnect a Google Fonts se usi Geist via CDN — vedi `tokens/fonts.css`.)

3. **Tema chiaro/scuro:** l'HTML radice porta `data-theme` e `data-anim`:
   ```html
   <html lang="it" data-theme="light" data-anim="piene">
   ```
   Il toggle tema cambia `document.documentElement.dataset.theme` tra `light` e `dark`.
   Persisti la scelta (localStorage o preferenza utente lato server).

4. **Allinea le classi dei template** a quelle che il CSS si aspetta (elenco sotto). Dove il
   markup già le usa, il nuovo look appare da solo. Dove diverge, aggiorna il template.

5. **Collega i dati reali.** Sostituisci ogni valore mock con i dati veri passati al template
   (es. `{{ patrimonio | euro }}`, loop `{% for r in portfolio.rows %}` ecc.). Vedi
   "Modello dati" sotto per la forma esatta dei dati che ogni schermata consuma.

---

## Schermate / Viste

Le schermate corrispondono ai file `*Screen.jsx.txt` in `design_reference/`. Per ognuna:
scopo, layout, componenti chiave e i dati che consuma.

### 1. Topbar (globale — su tutte le pagine)
- **Scopo:** navigazione + preferenze. Sempre sticky in alto.
- **Layout:** `.topbar > .topbar-inner` (max-width `--wrap-max`, padding `--wrap-pad`), flex,
  `gap: --space-4`, `min-height: --topbar-h`. Brand a sinistra, `.nav` al centro, `.prefs`
  spinto a destra (`margin-left:auto`).
- **Nav:** 7 voci — Home, Portafoglio, PAC, Analisi, Finanze, Notizie, Impostazioni. Voce attiva:
  `.nav a.active` → sfondo `--accent` (lime), testo `--on-accent`, glow lime. Hover: `--hover`.
- **Prefs:** `.theme-btn` (38×38, pill, icona sole/luna) + `.lang-select` (IT/UK).
- **Vetro liquido:** `background: --glass-bg-strong`, `backdrop-filter: blur(--glass-blur)`.

### 2. Dashboard / Home (`DashboardScreen.jsx.txt`)
- **Scopo:** colpo d'occhio sul patrimonio.
- **Layout:** riga stat `.mm-stats4` (grid `1.7fr 1fr 1fr`) con **hero** patrimonio totale
  (grande, con count-up) + 3 stat di supporto (investimenti, liquidità, saldo). Sotto: sparkline
  patrimonio a 12 mesi, prossimo PAC, top posizioni, riquadro sintesi AI.
- **Dati:** `patrimonio`, `perf12m`, `gain12m`, `updated`, `dash.patrimonioSerie` (12 punti €k),
  `dash.nextPac`, `dash.aiSummary`, `dash.aiConf`. Top posizioni da `portfolio.rows`.

### 3. Portafoglio (`PortfolioScreen.jsx.txt`)
- **Scopo:** tutte le posizioni (11 ETF + 3 azioni), con target vs. valore attuale.
- **Layout:** header con totale/perf/n. posizioni; `.table-wrap > table` con colonne
  Ticker · Nome · Categoria · Target% · Qtà · Prezzo · Valore · P/L%.
- **Interazioni:** "Aggiungi posizione" apre un form inline che **prepende** una riga; il cestino
  su una riga chiede conferma inline (reversibile). Click sul titolo/ticker → dettaglio posizione.
- **Dati:** `portfolio.{totale, perf, nPosizioni, nEtf, nAzioni, rows[]}`. Ogni riga:
  `{id, tk, tipo, name, cat, target, qty, prezzo, valore, pl, isin}`.

### 4. Dettaglio posizione (`PositionDetail.jsx.txt`, dati in `data-detail.js.txt`)
- **Scopo:** singolo titolo — grafico prezzo (con range selezionabili), scheda fondo, holdings
  look-through, "AI take".
- **Dati:** `data-detail.js` mappa per ticker holdings, serie prezzo, fund facts, nota AI.

### 5. Finanze (`FinanceScreen.jsx.txt`)
- **Scopo:** conti/carte, entrate-uscite, movimenti, spese per categoria.
- **Layout:** griglia wallet `.mm-wallets` (fino a 5 col.), cards conto/carta/contanti/PAC.
  Riquadro AI ✨ "scrivi a parole" (es. *"ieri 20€ di benzina con la carta"* → precompila il form).
  Form movimento; barre spese per categoria; tabella movimenti con conferma-per-eliminare.
- **Dati:** `finance.{patrimonio, entrate, uscite, saldo, fondoEmergenza, wallets[],
  speseCategoria[], movimenti[], categorie[]}`.

### 6. PAC (piano di accumulo) (in `MoreScreens.jsx.txt`)
- **Scopo:** ripartizione del versamento mensile per strumento.
- **Interazione:** cambia l'importo mensile → le quote si ricalcolano live.
- **Dati:** `pac.{importo, rows[] (target%, quota), fisse[], sommaQuote, sommaFissi, totale}`.

### 7. Analisi (`AnalisiScreen.jsx.txt`, dati in `data-analisi.js.txt`)
- **Scopo:** look-through per settore + metriche di rischio.
- **Dati:** `analisi.{settori[], techConc, divYield, effHoldings, risk{vol,mdd,sharpe,beta,...}}`.

### 8. Notizie (in `MoreScreens.jsx.txt`)
- **Scopo:** feed notizie in sola lettura con impatto/rilevanza/confidenza per ticker.
- **Dati:** `notizie.cards[]`: `{ticker, tipo, rilevanza, titolo, impatti[], conf, data, fonte}`.

### 9. Impostazioni (in `MoreScreens.jsx.txt`)
- **Scopo:** tema, lingua, animazioni — controllano davvero l'app (settano `data-theme` /
  `data-anim` / `lang` sul root).

---

## Vocabolario di classi (contratto CSS ↔ template)
Il CSS restilizza queste classi. I template Jinja devono usarle:
`.topbar .topbar-inner .brand .nav .nav a(.active/.disabled) .prefs .theme-btn .lang-select`
`.wrap .card .stat(.hero) .stat .v .pill .badge .btn .table-wrap table .form .note(.warn/.ok/.err)`
`.ai-box .disclaimer` — più gli helper di layout `.mm-stats4 .mm-grid-3 .mm-grid-2 .mm-wallets`
`.mm-wallet .mm-rowbtn .mm-titlebtn .mm-rangebtn .mm-aibtn` (vedi `design_reference/index.html.txt`).

## Design Tokens (estratto — valori completi in `styles/tokens/`)
- **Brand primario (pistacchio/lime):** `--lime-400 #A6DA47` (firma), `--accent = --lime-400`,
  testo su lime `--on-accent #1B2A05`, `--accent-strong --lime-600`.
- **Brand secondario (giallo pastello):** `--yellow-300 #F9DA5B` (firma), `--accent-2`.
- **Neutri caldi:** `--neutral-50 #F4F6EF` (bg), `--neutral-900 #181B14` (testo). Dark: `--bg #0E110C`.
- **Finanza:** guadagno `--pos #1E9E5A`, perdita `--neg #E2474A` (dark: `#46D588` / `#FF6B6B`).
- **AI:** famiglia giallo — `--ai --yellow-600`, `--ai-bg --yellow-50`.
- **Tipografia:** `--font-sans: Geist`; mono `Geist Mono` (ticker/ISIN). Base UI **15px**
  (`--text-base`), scala 11 → 60px. **Numeri sempre tabulari** (`--num: tabular-nums`) su ogni
  cella monetaria/quantità/percentuale.
- **Data-viz:** `--viz-1..6` (lime, giallo, teal `#5BB8C4`, neutro, arancio `#F0975B`, lime scuro).
- Raggi, ombre, glass e motion: vedi rispettivi file in `styles/tokens/`.

## Modello dati (forma dei dati reali da fornire ai template)
La struttura completa dei dati che ogni schermata consuma è documentata — con valori d'esempio —
in `design_reference/data.js.txt`, `data-detail.js.txt`, `data-analisi.js.txt`. Usala come
**contratto**: replicane le chiavi con i tuoi dati reali. Coerenza chiave: `patrimonio =
portfolio.totale + liquidità finanze`; le percentuali `target` del portafoglio sommano a 100.

## Formattazione (locale it-IT)
I formatter usati sono in `design_reference/helpers.jsx.txt` (`window.MMFmt`): euro con separatore
migliaia `.` e decimali `,`; percentuali con segno; date `gg/mm · HH:MM`. Nel backend usa
filtri Jinja equivalenti (es. Babel/`format_currency(x, 'EUR', locale='it_IT')`).

## Assets
- Logo/mark: `assets/logo-mark.svg`, favicon `assets/favicon.svg` (nel progetto design, da
  portare nella tua `static/`). Icone: geometrie stile Lucide, definite in
  `design_reference/icons.jsx.txt` (`<MMIcon name="…">`) — sostituibili con la tua libreria icone.

## Files inclusi in questo pacchetto
- `styles/styles.css` — entry (@import-only)
- `styles/mymoney.css` — foglio componenti (restyle classi Jinja)
- `styles/tokens/*.css` — tutti i token
- `design_reference/*.txt` — sorgenti React di riferimento (da leggere, non eseguire) + `data*`

> Suggerimento per Claude Code: apri questo README, poi `styles/` e `design_reference/data.js.txt`.
> Applica i CSS alla `static/`, allinea le classi nei template Jinja e sostituisci i mock con i
> dati veri seguendo il "Modello dati". Procedi una schermata alla volta partendo dalla Dashboard.
