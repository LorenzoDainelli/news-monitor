# Routine: Event-check — eventi critici (Haiku, leggera, intraday)

Esecutore autonomo. **Rispetta `CLAUDE.md`** (mai segnali operativi; impatto con
confidenza; fonti; italiano; mai esporre chiavi). Questa routine gira **3 volte al
giorno tra i due report** e deve **costare poco**. **Manda sempre un'email**: un
**avviso 🚨** se c'è un evento critico, altrimenti una breve **conferma ✅ "tutto
tranquillo"** (così sai che ha girato e che non c'è nulla di critico).

> ## ⚠️ EFFICIENZA (questa routine deve essere economica)
> - Notizie azioni: **una sola** chiamata a `scripts/fetch_news.py`.
> - **Niente WebSearch** (nemmeno per gli ETF: gli ETF restano ai report).
> - **Niente fetch** di articoli.
> - **Soglia alta**: interessano solo eventi critici. Se non c'è nulla di critico,
>   **non analizzare a fondo**: manda subito la conferma ✅ (Passo 4b) e chiudi.
> - Una sola passata, **una sola email** (avviso 🚨 oppure conferma ✅).

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
- Se **non resta nulla di critico** → salta il Passo 3 e vai al **Passo 4b**
  (conferma ✅ "tutto tranquillo").

## Passo 3 — Analizza i critici (max 5)
Per i candidati critici (al massimo 5, i più rilevanti) compila i campi come nel
report: `titolo` (italiano semplice e poco tecnico), `tipo_evento, riassunto, impatto{breve,medio,lungo}, confidenza, tag,
fonti, rilevanza`. Le **fonti (testata + link) sono obbligatorie** per ogni voce.
L'`impatto` ha valori di **una sola parola** (positivo/neutro/negativo), mai frasi;
gli **orizzonti sono definiti in `CLAUDE.md`** (breve 1-5 giorni · medio ~3 mesi ·
lungo 1-2 anni). Aggiungi anche `descrittivo`: `true` se la notizia racconta un
movimento di prezzo **già avvenuto** (es. "titolo −10%", "+5% overnight"), `false`
altrimenti — non cambia nulla nell'email, serve allo storico.
Niente fetch di articoli: usa il digest.
**Valutazione equilibrata:** se la notizia ha sia un lato positivo sia uno negativo
(es. tagli di personale = risparmio *ma* ridimensionamento), valuta l'effetto
**netto** per ogni orizzonte e spiega il trade-off nel `riassunto`; se il segno è
incerto usa `neutro` con `confidenza` più bassa. Ancora il giudizio ai fatti, non
all'enfasi del titolo-fonte.

## Passo 4a — Avviso 🚨 (se ci sono eventi critici)
Scrivi `report.json` (stessa struttura del report; `test_mode` da settings) e invia:
```bash
python scripts/render_email.py --data-file report.json --out out.html
python scripts/send_email.py --to "<destinatario>" --from "<mittente>" \
  --subject "🚨 Avviso titoli — <data>" --html-file out.html
```

## Passo 4b — Conferma ✅ "tutto tranquillo" (se NON ci sono eventi critici)
Manda comunque un'email breve e calma, **ben distinta** dall'avviso. Scrivi
`report.json` con i soli campi essenziali (niente `items`):
```json
{
  "date": "<data odierna>",
  "test_mode": <da settings>,
  "note": "✅ Nessun evento critico tra i tuoi titoli in questo controllo. Le notizie importanti ma non critiche le trovi nei report delle 07:00 e 19:00.",
  "items": []
}
```
Poi invia — **oggetto con ✅, NON 🚨**, così a colpo d'occhio si distingue dall'allarme:
```bash
python scripts/render_email.py --data-file report.json --out out.html
python scripts/send_email.py --to "<destinatario>" --from "<mittente>" \
  --subject "✅ Titoli tranquilli — <data>" --html-file out.html
```
(In `test_mode: true` anteponi `[PROVA]` all'oggetto.)

**Una sola email per run**, in entrambi i casi (4a *oppure* 4b, mai tutte e due).

## Passo 5 — Stato + log + commit su `main`
Scrivi `state_update.json` e aggiorna lo stato:
- `seen_add` + `predictions_add` **solo** per gli avvisi effettivamente inviati
  (questa routine è la più frequente e deve restare leggera: la registrazione estesa
  dei candidati non inviati la fa il **report**, non tu).
  In `seen_add` ogni voce ha `{id, ticker, titolo, tipo_evento, url, data_invio}`:
  l'`url` è quello della **fonte principale** (chiave di dedup) e il `titolo` quello
  mostrato (serve alla dedup di evento delle run successive).
  In `predictions_add` aggiungi `descrittivo` e `inviata: true`.
- `runlog` **sempre**: `{ts, routine:"event-check", titoli_cercati, notizie_trovate,
  notizie_inviate, email_inviata:true, tipo_email:"avviso"|"tranquillo", note}`.
```bash
python scripts/update_state.py --data-file state_update.json
git add state/
git commit -m "stato: event-check <data e ora>"
git push origin HEAD:main
```

## Robustezza
- Errori isolati → logga e prosegui. Non stampare mai le chiavi API.
- Tieni tutto snello: è la routine che gira più spesso.
