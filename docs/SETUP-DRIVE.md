# Collegare MyMoney al tuo Google Drive (Fase 5) — guida passo-passo

> Tempo: ~10 minuti, una volta sola. Serve il TUO account Google: per questo
> lo fai tu (io non posso creare account o credenziali al posto tuo).
> Alla fine avrai: il PC e l'iPhone che si sincronizzano attraverso una
> cartellina NASCOSTA del tuo Drive, che solo MyMoney può vedere
> (scope `drive.appdata`: l'app non vede i tuoi file personali).

## Passo 1 — Crea il progetto Google Cloud (gratuito)

1. Vai su <https://console.cloud.google.com> e accedi col tuo account Google.
2. In alto a sinistra, clic sul selettore progetti → **Nuovo progetto**.
3. Nome: `MyMoney` (o quello che vuoi) → **Crea**. Seleziona il progetto.

## Passo 2 — Attiva l'API di Google Drive

1. Menu ☰ → **API e servizi** → **Libreria**.
2. Cerca **Google Drive API** → aprila → **Abilita**.

## Passo 3 — Schermata di consenso OAuth (modalità test: basta per uso personale)

1. Menu ☰ → **API e servizi** → **Schermata consenso OAuth**
   (se compare "Google Auth Platform", è la stessa cosa).
2. Tipo di utente: **Esterno** → Crea.
3. Nome app: `MyMoney` · email di assistenza: la tua · contatto sviluppatore: la tua.
   Salva e continua (gli altri campi si possono lasciare vuoti).
4. **Ambiti (scopes)**: puoi saltare (l'app lo chiede da sola). Avanti.
5. **Utenti di test**: aggiungi la TUA email (`lorenzodainelli08@gmail.com`).
   ⚠️ Questo passo è importante: in modalità Testing solo gli utenti di test
   possono dare il consenso. Salva.
6. NON serve "pubblicare" l'app né alcuna verifica di Google: resta in Testing.
   (Nota: in Testing i refresh token scadono dopo ~6 mesi di inutilizzo — se
   capita, si ricollega con un clic, i dati non si toccano.)

## Passo 4 — Credenziali per il PC (client "Desktop")

1. **API e servizi** → **Credenziali** → **Crea credenziali** → **ID client OAuth**.
2. Tipo di applicazione: **App desktop**. Nome: `MyMoney PC` → Crea.
3. Ti mostra **ID client** (finisce con `.apps.googleusercontent.com`) e
   **Client secret** (inizia con `GOCSPX-`). Copiali.
4. Apri MyMoney sul PC → **Impostazioni** → card **Sincronizzazione Google
   Drive** → incolla ID client e secret → **Salva credenziali**.
5. Clic su **Collega Google Drive**: si apre Google, scegli il tuo account e
   accetta (vedrai l'avviso "app non verificata": è la TUA app in modalità
   test → "Continua"). Tornerai sull'app con "Drive collegato!".
6. Prova: **Sincronizza ora** → deve dire "Sincronizzazione completata".

> Dove finiscono le credenziali? Nel database locale in `app/data/`
> (cartella NON committata su GitHub). Mai nei log, mai nel repo.

## Passo 5 — Credenziali per l'iPhone (client "Web")

La PWA gira nel browser: usa un secondo client, di tipo Web (senza secret).

1. **Credenziali** → **Crea credenziali** → **ID client OAuth** →
   tipo **Applicazione web**. Nome: `MyMoney PWA`.
2. **Origini JavaScript autorizzate** → Aggiungi URI: l'indirizzo della tua
   PWA su Cloudflare Pages, es. `https://TUO-SITO.pages.dev`
   (senza barra finale).
3. **URI di reindirizzamento autorizzati** → Aggiungi URI: lo STESSO indirizzo
   con la barra finale, es. `https://TUO-SITO.pages.dev/`.
   (Se vuoi provare anche dal PC in locale, aggiungi pure
   `http://127.0.0.1:8000/pwa/` a entrambe le liste.)
4. Crea → copia l'**ID client** (il client Web per questo flusso non usa il secret).
5. Sull'iPhone apri MyMoney (la PWA installata) → tocca **☁️ Drive** →
   incolla l'ID client → **Salva e collega** → consenso Google → torni
   nell'app e la prima sincronizzazione parte da sola.

## Da quel momento in poi

- **PC**: sincronizza da Impostazioni ("Sincronizza ora") e comunque da solo
  a ogni avvio dell'app.
- **iPhone**: tocca ☁️ Drive quando vuoi allineare. Se il "pass" di Google è
  scaduto (dura ~1 ora), il tocco successivo ripassa un attimo da Google e
  riparte — se la sessione è attiva è questione di un secondo.
- **Revocare l'accesso**: da Google (<https://myaccount.google.com/permissions>)
  o col bottone "Scollega" sul PC. I dati locali NON si perdono mai: si
  interrompe solo il corriere.
- **Fallback senza Drive**: i bottoni 📤 Esporta / 📥 Importa restano sempre lì
  (file manuale, utile anche come backup).

## Se qualcosa non va

| Sintomo | Causa probabile | Rimedio |
|---|---|---|
| "Accesso bloccato: app non verificata" senza tasto Continua | la tua email non è tra gli utenti di test | Passo 3.5 |
| `redirect_uri_mismatch` sull'iPhone | l'URI registrato non coincide ESATTAMENTE con l'indirizzo della PWA | Passo 5.3 (occhio a https e barra finale) |
| `redirect_uri_mismatch` sul PC | il client del PC non è di tipo "App desktop" | Passo 4.2 |
| Il PC dice "Accesso scaduto o revocato" | refresh token revocato/scaduto | clic su Collega Google Drive, un secondo consenso |
| Sync ok ma sull'altro dispositivo non arriva nulla | l'altro dispositivo non ha ancora sincronizzato | sincronizza ANCHE lì (il corriere consegna solo a chi passa a ritirare) |
