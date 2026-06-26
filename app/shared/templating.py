"""Configurazione unica dei template (HTML) con i filtri di formattazione.

Importato da tutte le pagine, cosi' lo stile e i filtri (€, %, quantita') sono
identici ovunque.
"""
from fastapi.templating import Jinja2Templates

from shared.config import APP_DIR
from shared import formatting
from shared import i18n, prefs


def _global_context(request):
    """Inietta in OGNI pagina: traduttore (t), lingua e tema correnti, elenco lingue
    e il percorso corrente (per tornare qui dopo aver cambiato lingua/tema)."""
    lang = prefs.get_lang()
    return {
        "t": i18n.make_translator(lang),
        "lang": lang,
        "theme": prefs.get_theme(),
        "LANGS": i18n.LANGS,
        "cur_path": request.url.path,
    }


templates = Jinja2Templates(directory=str(APP_DIR / "templates"),
                            context_processors=[_global_context])
templates.env.filters["eur"] = formatting.format_eur
templates.env.filters["pct"] = formatting.format_pct
templates.env.filters["qty"] = formatting.format_qty
templates.env.filters["big"] = formatting.format_compact
