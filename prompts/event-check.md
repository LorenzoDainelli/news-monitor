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

## Passo 1 — Config e stato
Leggi `config/settings.yaml`, `config/portfolio.yaml` (solo per i ticker delle
azioni), `state/seen.json`.

## Passo 2 — Scarica e filtra (solo critici)
- Estrai i ticker `tipo: azione` ed esegui **una** chiamata:
  `python scripts/fetch_news.py --tickers TICK1,...,TICKn`
- Dal digest tieni **solo** gli eventi critici, cioè con `rilevanza >=
  soglia_evento_critico` (da settings) **e/o** di tipo critico: earnings con
  sorpresa, M&A, revisione guidance, cambio CEO, evento regolatorio grave,
  downgrade/upgrade forte.
- Scarta ciò che è già in `seen.json` (non riallertare ciò che un report ha già
  mandato).
- Se **non resta nulla** → niente email. Vai direttamente al Passo 5 (solo log).

## Passo 3 — Analizza i critici (max 3)
Per i candidati critici (al massimo 3, i più rilevanti) compila i campi come nel
report: `titolo` (italiano semplice e poco tecnico), `tipo_evento, riassunto, impatto{breve,medio,lungo}, confidenza, tag,
fonti, rilevanza`. Le **fonti (testata + link) sono obbligatorie** per ogni voce.
L'`impatto` ha valori di **una sola parola** (positivo/neutro/negativo), mai frasi.
Niente fetch di articoli: usa il digest.

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
- `seen_add` + `predictions_add` **solo** per gli avvisi effettivamente inviati;
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
