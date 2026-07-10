# UI Kit — MyMoney app

High-fidelity, click-through recreation of the MyMoney personal-finance web app
(Flask + Jinja2 backend). Every screen is built from the design-system
components and tokens — same class vocabulary the backend renders, so it stays
a faithful preview of production.

## Run
Open `index.html`. It loads the compiled `_ds_bundle.js`, the shared data,
icons and screen modules, then mounts an interactive shell.

## What's interactive
- **Top bar** — 7-item nav with a visible active state, theme toggle (light/dark),
  language select. You always know where you are.
- **Dashboard** — patrimonio totale counts up and dominates; investimenti, liquidità
  and saldo follow; sparkline + top positions.
- **Portafoglio** — positions table; "Aggiungi posizione" opens a short inline form
  that prepends a row; delete asks for an inline confirm (reversible).
- **Finanze** — wallet cards, the ✨ "scrivi a parole" AI box (type *"ieri 20€ di
  benzina con la carta"* → the form pre-fills), movimento form, expenses-by-category,
  movements table with confirm-to-delete.
- **PAC** — change the monthly amount → quotas recompute live.
- **Analisi** — look-through sector bars + risk metrics.
- **Notizie** — read-only news feed with impact/relevance/confidence.
- **Impostazioni** — theme / language / animations actually drive the app.

## Files
- `index.html` — shell (nav, theme/lang/anim state, screen routing)
- `data.js` — mock data (`window.MM_DATA`), consistent across screens
- `helpers.jsx` — it-IT formatters (`window.MMFmt`) + nav config (`window.MM_NAV`)
- `icons.jsx` — Lucide-geometry icon set (`<MMIcon name="…">`)
- `DashboardScreen.jsx`, `PortfolioScreen.jsx`, `FinanceScreen.jsx`, `MoreScreens.jsx`

These are cosmetic recreations: data is mocked, no network. The point is visual +
interaction fidelity, composing the real components — not re-implementing them.
