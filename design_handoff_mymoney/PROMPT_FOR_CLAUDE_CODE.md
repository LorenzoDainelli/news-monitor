# Prompt da incollare a Claude Code

Copia il testo qui sotto (nel blocco) e incollalo a Claude Code, dopo aver messo la cartella
`design_handoff_mymoney/` nella root del tuo repo Flask.

---

```
Nel repo trovi la cartella design_handoff_mymoney/ con il nuovo design dell'app MyMoney.
Voglio applicare questo design all'app reale e collegarlo ai dati veri, così tutto funziona
e si aggiorna dinamicamente.

Contesto: la mia app è Flask + Jinja2. Il redesign NON riscrive il markup — restilizza lo
stesso vocabolario di classi che i miei template già usano (.topbar .nav .card .stat .pill
.badge .btn .table-wrap .form .note .ai-box ecc.).

Prima di scrivere codice:
1. Leggi design_handoff_mymoney/README.md per intero.
2. Leggi design_handoff_mymoney/design_reference/data.js.txt (e data-detail / data-analisi):
   è il "contratto" della forma dei dati che ogni schermata consuma.
3. Ispeziona il MIO codebase: dove sono i template Jinja, il CSS statico attuale, i modelli/
   query che forniscono i dati (patrimonio, portafoglio, movimenti, PAC, analisi, notizie).

Poi procedi così, UNA SCHERMATA ALLA VOLTA, partendo dalla Dashboard/Home:
A. Installa i CSS: copia design_handoff_mymoney/styles/ in app/static/ e fai in modo che il
   layout base linki UN SOLO file, styles.css (fa @import di token + mymoney.css in ordine).
   Aggiungi data-theme="light" e data-anim="piene" sull'<html>.
B. Allinea le classi del template alla schermata di riferimento (vedi il .jsx.txt corrispondente
   e la sezione "Vocabolario di classi" del README).
C. COLLEGA I DATI REALI: sostituisci ogni valore/loop finto con i miei dati veri passati al
   template dal backend (query/ORM/route esistenti). Usa i miei dati, mai i mock del riferimento.
D. Implementa le interazioni descritte (aggiungi/elimina posizione con conferma, form movimento,
   ricalcolo PAC live, toggle tema/lingua che scrivono su data-theme/lang e vengono persistiti).
E. Formattazione locale it-IT (euro 1.234,56 · percentuali con segno · date gg/mm · HH:MM) con
   filtri Jinja equivalenti a quelli in helpers.jsx.txt (window.MMFmt).

Regole:
- I file in design_reference/ sono SOLO riferimento da leggere (sono .txt apposta): non
  eseguirli, non introdurre React nell'app. L'unica cosa da copiare in produzione è styles/.
- Rispetta i miei pattern esistenti (routing, template, accesso ai dati, autenticazione).
- Non inventare dati o endpoint: se manca una fonte dati per un valore mostrato nel design,
  fermati e chiedimi da dove prenderlo.
- Fammi rivedere ogni schermata prima di passare alla successiva.

Comincia elencando le schermate del design mappate ai file/route del mio repo, e dimmi cosa ti
serve da me (percorsi, come si chiamano i modelli dati) prima di modificare i file.
```

---

## Note per te (non per Code)
- Sostituisci nel prompt i dettagli che conosci del tuo repo (es. "i template stanno in
  `app/templates/`", "i dati del portafoglio arrivano dal modello `Position`") per farlo partire
  più veloce e senza domande.
- Se la tua app **non** è Flask/Jinja ma un altro stack (es. React/Vue reale), dillo a Code:
  in quel caso `styles/` resta valido come token/CSS, ma le schermate vanno ricreate come
  componenti nel tuo framework, usando i `.jsx.txt` come riferimento più diretto.
