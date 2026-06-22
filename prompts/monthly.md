# Routine: Digest mensile (Opus, mensile) — visione d'insieme del mese

Esecutore autonomo. **Rispetta `CLAUDE.md`** (mai segnali operativi; impatto con
confidenza; fonti; italiano; mai esporre chiavi). **INVIA SEMPRE** (è il resoconto
mensile). Non usa la news API: lavora sullo **stato raccolto nel mese**. Sei su
**Opus**: usa la profondità per una **sintesi d'insieme** ragionata, non un elenco.

## Passo 1 — Carica stato e config
Leggi `config/settings.yaml`, `config/portfolio.yaml`, `state/seen.json`,
`state/predictions.json`, `state/runlog.ndjson`.

## Passo 2 — Calcola (ultimi ~30 giorni)
- **Statistiche**: dal `runlog` quante run ed email nel mese.
- **Top notizie del mese**: da `predictions.json` (ultimi 30 giorni) le **8-12 più
  rilevanti** (per `rilevanza`) → `items`. **Copia `impatto` (oggetto
  {breve,medio,lungo}) e `confidenza` ESATTAMENTE come sono in `predictions.json`
  — NON rimetterli a "neutro".**
- **Temi del mese**: aggrega i `tag` delle notizie del mese → quali temi/settori si
  sono mossi di più (es. "AI/semiconduttori molto attivi, difesa in evidenza").
- **Titoli tranquilli del mese**: titoli di `portfolio.yaml` senza alcuna voce in
  `seen.json` negli ultimi 30 giorni → `quiet = {"azioni":[nomi], "etf":[nomi brevi]}`.
  **Azioni**: usa il `nome`. **ETF**: usa SEMPRE questi nomi brevi (mai il ticker) —
  IWDA=Core MSCI World, CSPX=S&P 500, CNDX=Nasdaq 100, VHYL=High Dividend,
  XDWH=World Health Care, NATO=Future of Defence, NUKL=Uranio & Nucleare,
  XDWM=World Materials, GIFL=Global Infrastructure, UKRN=Ukraine Reconstruction,
  HEAL=Healthcare Innovation.

## Passo 3 — Costruisci `report.json` e invia
```json
{
  "date": "mese di <mese> <anno>",
  "test_mode": <da settings>,
  "note": "<sintesi d'insieme del mese in 2-3 frasi: andamento generale a livello di notizie e temi del portafoglio, con disclaimer. Includi l'heartbeat: N run e M email nel mese.>",
  "items": [ { ...le top notizie del mese... } ],
  "quiet": {"azioni": ["..."], "etf": ["..."]}
}
```
Poi:
```bash
python scripts/render_email.py --data-file report.json --out out.html
python scripts/send_email.py --to "<destinatario>" --from "<mittente>" \
  --subject "📅 Riepilogo mensile — <mese>" --html-file out.html
```
**Una sola email.**

## Passo 4 — Log e commit su `main`
`state_update.json` col solo `runlog` (routine `"monthly"`). Poi:
```bash
python scripts/update_state.py --data-file state_update.json
git add state/ && git commit -m "stato: monthly <mese>" && git push origin HEAD:main
```

## Efficienza
- **Niente `fetch_news.py`, niente WebSearch** (usi lo stato già raccolto).
- Una sola passata, una sola email.
