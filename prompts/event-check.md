# Routine: Event-check — eventi critici (Haiku, leggera, intraday)

Esecutore autonomo. **Rispetta `CLAUDE.md`** (mai segnali operativi; impatto con
confidenza; fonti; italiano; mai esporre chiavi). Questa routine gira **3 volte al
giorno tra i due report** e deve **costare poco**: invia un'email **solo** per
eventi davvero critici, altrimenti salta.

> ## ⚠️ EFFICIENZA (questa routine deve essere economica)
> - Notizie azioni: **una sola** chiamata a `scripts/fetch_news.py`.
> - **Niente WebSearch** (nemmeno per gli ETF: gli ETF restano ai report).
> - **Niente fetch** di articoli.
> - **Soglia alta**: interessano solo eventi critici. Se non c'è nulla, **salta in
>   fretta** senza analizzare oltre.
> - Una sola passata, una sola eventuale email.

## Passo 1 — Config
Leggi `config/settings.yaml` e `config/portfolio.yaml` (solo per i ticker delle
azioni). **NON** leggere `state/seen.json`: la dedup è gestita dallo script al
Passo 2.

## Passo 2 — Scarica e filtra (solo critici)
- Estrai i ticker `tipo: azione` ed esegui **una** chiamata (passa SEMPRE
  `--seen-file`, è ciò che evita i doppioni):
  `python scripts/fetch_news.py --tickers TICK1,...,TICKn --seen-file state/seen.json`
  Lo script restituisce `items` (già ripuliti dalle notizie con URL già inviato) e
  `recent_seen` (le notizie già inviate negli ultimi giorni, con `ticker` e `titolo`).
- Dal digest tieni **solo** gli eventi critici, cioè con `rilevanza >=
  soglia_evento_critico` (da settings) **e/o** di tipo critico: earnings con
  sorpresa, M&A, revisione guidance, cambio CEO, evento regolatorio grave,
  downgrade/upgrade forte.
- **DEDUP DI EVENTO (obbligatoria):** confronta ogni candidato con `recent_seen`.
  Se lo **stesso evento** (stessa azienda + stesso fatto, es. "Oracle taglia 21.000
  posti") è già stato inviato — **anche da una fonte/URL diverso, anche con un
  punteggio diverso** — **scartalo**. Lo script toglie già i doppioni di URL; tu
  togli i doppioni di *evento*. Nel dubbio, stesso fatto = non reinviare.
- Se **non resta nulla** → niente email. Vai direttamente al Passo 5 (solo log).

## Passo 3 — Analizza i critici (max 3)
Per i candidati critici (al massimo 3, i più rilevanti) compila i campi come nel
report: `titolo` (italiano semplice e poco tecnico), `tipo_evento, riassunto, impatto{breve,medio,lungo}, confidenza, tag,
fonti, rilevanza`. Le **fonti (testata + link) sono obbligatorie** per ogni voce.
L'`impatto` ha valori di **una sola parola** (positivo/neutro/negativo), mai frasi.
Niente fetch di articoli: usa il digest.
**Valutazione equilibrata:** se la notizia ha sia un lato positivo sia uno negativo
(es. tagli di personale = risparmio *ma* ridimensionamento), valuta l'effetto
**netto** per ogni orizzonte e spiega il trade-off nel `riassunto`; se il segno è
incerto usa `neutro` con `confidenza` più bassa. Ancora il giudizio ai fatti, non
all'enfasi del titolo-fonte.

## Passo 4 — Avviso email (solo se ci sono critici)
Scrivi `report.json` (stessa struttura del report; `test_mode` da settings) e invia:
```bash
python scripts/render_email.py --data-file report.json --out out.html
python scripts/send_email.py --to "<destinatario>" --from "<mittente>" \
  --subject "🚨 Avviso titoli — <data>" --html-file out.html
```
**Una sola email.** Se in `test_mode: true` non ci sono critici, invia comunque un
breve avviso diagnostico (`items: []`, compila `diagnostic`).

## Passo 5 — Stato + log + commit su `main`
Scrivi `state_update.json` e aggiorna lo stato:
- `seen_add` + `predictions_add` **solo** per gli avvisi effettivamente inviati.
  In `seen_add` ogni voce ha `{id, ticker, titolo, tipo_evento, url, data_invio}`:
  l'`url` è quello della **fonte principale** (chiave di dedup) e il `titolo` quello
  mostrato (serve alla dedup di evento delle run successive).
- `runlog` **sempre** (anche con 0 critici): `{ts, routine:"event-check",
  titoli_cercati, notizie_trovate, notizie_inviate, email_inviata, note}`.
```bash
python scripts/update_state.py --data-file state_update.json
git add state/
git commit -m "stato: event-check <data e ora>"
git push origin HEAD:main
```

## Robustezza
- Errori isolati → logga e prosegui. Non stampare mai le chiavi API.
- Tieni tutto snello: è la routine che gira più spesso.
