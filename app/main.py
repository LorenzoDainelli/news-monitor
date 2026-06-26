"""Punto di avvio dell'app (FastAPI).

Crea le tabelle, precarica il portafoglio la prima volta, collega le pagine.
Si avvia con run.py (o col doppio click su Avvia-Finanza.bat).
"""
import threading

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from shared.config import APP_DIR, APP_NAME
from shared.db import Base, engine
from shared.templating import templates

# Importa i modelli PRIMA di create_all, cosi' le tabelle vengono registrate.
import shared.settings_store          # noqa: F401  -> tabella shared_settings
import portfolio.models               # noqa: F401  -> tabella portfolio_positions
from portfolio import market          # noqa: F401  -> tabella portfolio_quotes

from portfolio import seed
from portfolio import service as pf_service
from portfolio.routes import router as portfolio_router
from shared.settings_routes import router as settings_router
from shared.prefs_routes import router as prefs_router

# --- preparazione database (una tantum) ---
Base.metadata.create_all(bind=engine)
seed.seed_if_empty()


# --- aggiornamento prezzi all'apertura, in background (non blocca l'avvio) ---
def _refresh_prezzi_bg():
    try:
        if market.is_stale():
            market.refresh_all()
        market.refresh_all_fundamentals()   # holdings/settori/dividendi (cache 24h)
    except Exception:
        pass  # mai far fallire l'avvio per i prezzi: si riproverà


threading.Thread(target=_refresh_prezzi_bg, daemon=True).start()

# --- app web ---
app = FastAPI(title=APP_NAME)
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")
app.include_router(portfolio_router)
app.include_router(settings_router)
app.include_router(prefs_router)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {
        "active": "home",
        "r": pf_service.riepilogo(),
    })
