# Monitor titoli — sistema personale di notizie ed earnings

Strumento personale che monitora un portfolio di titoli, cerca le notizie rilevanti
durante l'esecuzione di una **Routine di Claude Code** (nel cloud Anthropic) e invia
un report via **email** — solo se c'è qualcosa di rilevante.

Filosofia: **ridurre il rumore** e **onestà intellettuale**. Nessun segnale
operativo, nessuna previsione di prezzo; analisi qualitative con disclaimer e
livello di confidenza.

> **Stato: FASE 1** — un titolo, un'email di prova, per validare l'idraulica
> (invio email + accesso di rete + scrittura dello stato). Le altre funzionalità
> arrivano nelle fasi successive.

## Come funziona (in breve)
1. Una Routine schedulata parte nel cloud (PC spento OK).
2. Clona questo repo (config + prompt + stato).
3. Segue `prompts/report.md`: cerca notizie, filtra, deduplica, riassume.
4. Se c'è qualcosa di rilevante (o se `test_mode: true`), invia l'email via Resend.
5. Aggiorna lo stato (`state/`) e fa `git commit` per ricordarsene alla run dopo.

## Struttura del repo
```
CLAUDE.md              regole sempre attive (mai segnali operativi, disclaimer, ...)
config/
  portfolio.yaml       i titoli monitorati (Fase 1: uno solo)
  settings.yaml        destinatario, mittente, soglie, test_mode
prompts/
  report.md            istruzioni passo-passo della routine
scripts/
  send_email.py        invio email via API Resend (solo stdlib, nessuna dipendenza)
state/
  seen.json            notizie già inviate (deduplicazione/idempotenza)
  runlog.ndjson        una riga per run (audit + health-check)
```

---

## Setup una tantum

### 1) Repo GitHub privato
Crea un repo **privato** e carica questi file (`git init`, commit, push, oppure
`gh repo create`). Privato = portfolio e ISIN restano riservati.

### 2) Chiave Resend
- Crea un account su https://resend.com e genera una **API key**.
- Avvio rapido: con il mittente `onboarding@resend.dev` Resend consente l'invio
  **solo verso l'email con cui ti sei registrato**. Per inviare da/verso altri
  indirizzi, verifica un tuo dominio e aggiorna `mittente` in `settings.yaml`.

### 3) Collega GitHub a Claude Code
Nel terminale Claude Code esegui `/web-setup` per dare accesso al repo.

### 4) Crea l'ambiente cloud della routine
Su https://claude.ai/code/routines, in fase di creazione routine, apri le
impostazioni dell'ambiente:
- **Network access → Custom**: aggiungi `api.resend.com` e spunta "Also include
  default list of common package managers".
- **Environment variables**: aggiungi `RESEND_API_KEY=<la tua chiave>`
  (formato `.env`, senza virgolette).

### 5) Crea la routine
- **Prompt** (campo della routine): testo breve che punta al repo —
  > Leggi e segui le istruzioni in `prompts/report.md`. Rispetta `CLAUDE.md`.
- **Repository**: questo repo.
- **Environment**: quello configurato al punto 4.
- **Permissions**: abilita **Allow unrestricted branch pushes** (così i commit di
  stato arrivano su `main`).
- **Trigger**: per il test usa **Run now** (a regime imposteremo gli orari).

### 6) Test Fase 1
Lancia **Run now**. Verifica:
- ✅ arriva l'**email di prova** (controlla anche spam);
- ✅ nel repo compare un nuovo **commit** con `state/runlog.ndjson` aggiornato;
- apri la sessione della run per leggere cosa ha fatto e diagnosticare eventuali
  errori (es. dominio non in whitelist → `403 host_not_allowed`).

Quando il test passa, si procede con la Fase 2.
