# MyMoney — guscio PWA (v2)

Questa cartella è l'app installabile sul telefono (Fase 2 del [PIANO-V2](../PIANO-V2.md)).
È **statica**: HTML + CSS + JS + service worker + icone. **Nessun dato** finanziario
vive qui — i dati staranno nel telefono (IndexedDB, Fase 3) e nel tuo Google Drive
(sync, Fase 4).

## Provarla in locale (dal PC)
Con l'app avviata (`Avvia-Finanza.bat`), apri: `http://127.0.0.1:8000/pwa/`
Se il PC è raggiungibile mostra i tuoi portafogli reali; altrimenti lo stato "vuoto".

## Pubblicarla su Cloudflare Pages (gratis) e installarla su iPhone

1. Vai su **dash.cloudflare.com** → crea un account gratuito (o accedi).
2. Menu **Workers & Pages** → **Create** → **Pages** → **Connect to Git**.
3. Autorizza GitHub e scegli il repo **news-monitor** (privato: va bene).
4. Impostazioni build:
   - **Framework preset**: *None*
   - **Build command**: *(lascia vuoto)*
   - **Build output directory**: `pwa`
5. **Save and Deploy**. Dopo ~1 minuto avrai un indirizzo tipo
   `https://news-monitor-xxx.pages.dev`.
6. Sull'**iPhone**, apri quell'indirizzo con **Safari** → tocca **Condividi**
   → **Aggiungi alla schermata Home**. Comparirà l'icona MyMoney; si apre a
   schermo intero e funziona anche offline.

> Ad ogni push su GitHub, Cloudflare ripubblica il guscio da solo.

## Note tecniche
- Percorsi **relativi**: funziona sia sotto `/pwa/` (in locale) sia alla radice
  (su Cloudflare).
- `sw.js` mette in cache il guscio (apertura offline); l'API `/api/...` passa
  sempre dalla rete.
- Per far leggere alla PWA l'API del PC in LAN si può impostare in console:
  `localStorage.setItem('mm_api_base','http://IP-DEL-PC:8000')` (opzionale).
