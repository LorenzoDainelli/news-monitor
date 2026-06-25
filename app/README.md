# App finanza personale (locale)

Applicazione personale che unisce **portafoglio investimenti** e (in arrivo)
**finanze personali**, con un agente AI condiviso. Gira in locale sul PC, gratis,
e si apre nel browser. Vive nello stesso repo del news-monitor, ma è separata:
il robot-notizie continua a girare per conto suo nel cloud, l'app lo leggerà soltanto.

## Come si avvia
Doppio click su **`Avvia-Finanza.bat`** (nella cartella sopra a questa).
- Il **primo avvio** prepara l'ambiente e installa le librerie (~1 minuto, solo la prima volta).
- Poi si apre il browser su <http://127.0.0.1:8000>.
- Per **chiudere**: chiudi la finestra nera.

Serve solo **Python 3** già installato (verificato: 3.11). Nessun'altra installazione.

## Cosa c'è adesso (Fase 1)
- **Portafoglio**: 36 titoli + Take-Two precaricati; aggiungi/modifica/elimina da interfaccia.
- **Calcolatore PAC**: ripartisce l'importo mensile per % target, con controlli su 100% e arrotondamenti.
- **Impostazioni**: inserimento chiavi API (opzionali), salvate solo in locale.
- Tutto **offline**: nessun dato da internet in questa fase.

## Prossime fasi
2. Prezzi e dati di mercato (yfinance + Stooq, Finnhub free) · dashboard look-through · metriche di rischio.
3. Finanze personali: portafogli, entrate/uscite, trasferimenti, categorie.
4. Agente AI condiviso (Gemini) con filtro privacy per sezione.
5. Sezione Notizie: legge il report del news-monitor con le stesse card delle email.

## Struttura
```
app/
  main.py            avvio FastAPI, collega le pagine
  run.py             fa partire il server e apre il browser
  requirements.txt   librerie (gratuite)
  shared/            database, config, stile, impostazioni, formattazione
  portfolio/         posizioni, precarico, calcolatore PAC
  finance/           (Fase 3)
  templates/         pagine HTML (stile delle email)
  static/            style.css (il linguaggio visivo navy/grigi)
  data/              database locale + chiavi  ← MAI su GitHub (.gitignore)
```

## Privacy
- I dati finanziari e le chiavi API stanno **solo** in `app/data/` (escluso dal repo).
- Il server ascolta solo su `127.0.0.1` (il PC stesso), non è esposto alla rete.
- Nessun dato esce dal PC finché non attiverai l'agente AI (e anche allora con filtro privacy).
