# Routine: Digest settimanale (Sonnet, weekend) — heartbeat + riepilogo + titoli tranquilli

Esecutore autonomo. **Rispetta `CLAUDE.md`** (mai segnali operativi; impatto con
confidenza; fonti; italiano; mai esporre chiavi). Questa routine **INVIA SEMPRE**:
è anche l'**heartbeat** del sistema (se la domenica non arriva, vuol dire che
qualcosa è rotto). Non usa la news API: lavora sullo **stato già raccolto** durante
la settimana, quindi è economica.

## Passo 1 — Carica stato e config
Leggi `config/settings.yaml`, `config/portfolio.yaml`, `state/seen.json`,
`state/predictions.json`, `state/runlog.ndjson`.

## Passo 2 — Calcola gli elementi della settimana (ultimi 7 giorni)
- **Heartbeat/statistiche**: dal `runlog.ndjson` conta quante run ci sono state e
  quante email inviate negli ultimi 7 giorni.
- **Top notizie della settimana**: dalle voci di `predictions.json` con `data`
  negli ultimi 7 giorni, prendi le **5-8 più rilevanti** (per `rilevanza`).
  Diventano gli `items` (hai già: tipo_evento, impatto, confidenza, rilevanza,
  titolo, url; aggiungi un `riassunto` di 1 frase se utile).
- **Titoli tranquilli**: i titoli di `portfolio.yaml` che **non** compaiono in
  nessuna voce di `seen.json` negli ultimi 7 giorni → lista `quiet` (usa il ticker
  o il nome breve). È il "questa settimana è stato tranquillo".

## Passo 3 — Costruisci `report.json` e invia
Struttura (stessa del report, con i campi extra `note` e `quiet`):
```json
{
  "date": "settimana del <data>",
  "test_mode": <da settings>,
  "note": "✅ Sistema attivo: <N> run e <M> email negli ultimi 7 giorni. <1 frase di sintesi della settimana>.",
  "items": [ { ...le top notizie della settimana... } ],
  "quiet": ["TICK1","TICK2", "..."]
}
```
Poi:
```bash
python scripts/render_email.py --data-file report.json --out out.html
python scripts/send_email.py --to "<destinatario>" --from "<mittente>" \
  --subject "🗓️ Riepilogo settimanale — <settimana>" --html-file out.html
```
**Una sola email.** (Anche se non c'è nulla di rilevante, l'email parte lo stesso:
heartbeat + titoli tranquilli.)

## Passo 4 — Log e commit su `main`
Scrivi `state_update.json` col solo `runlog` (routine `"weekly"`); NON serve
`seen_add` (le notizie sono già in `seen.json`). Poi:
```bash
python scripts/update_state.py --data-file state_update.json
git add state/ && git commit -m "stato: weekly <settimana>" && git push origin HEAD:main
```

## Efficienza
- **Niente `fetch_news.py`, niente WebSearch** (usi lo stato già raccolto).
  Al massimo 1 WebSearch per una riga di contesto macro, se davvero utile.
- Una sola passata, una sola email.
