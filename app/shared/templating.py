"""Configurazione unica dei template (HTML) con i filtri di formattazione.

Importato da tutte le pagine, cosi' lo stile e i filtri (€, %, quantita') sono
identici ovunque.
"""
from fastapi.templating import Jinja2Templates

from shared.config import APP_DIR
from shared import formatting

templates = Jinja2Templates(directory=str(APP_DIR / "templates"))
templates.env.filters["eur"] = formatting.format_eur
templates.env.filters["pct"] = formatting.format_pct
templates.env.filters["qty"] = formatting.format_qty
