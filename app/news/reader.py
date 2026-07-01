"""Lettura delle notizie dal news-monitor (sezione Notizie, Fase 5).

Il robot-notizie gira nel cloud e committa lo stato in `state/` alla radice del
repo. Qui leggiamo `state/predictions.json` (le notizie analizzate, con impatto,
confidenza e rilevanza) e prepariamo card pronte da mostrare, nello stesso stile
visivo delle email. **Sola lettura**: l'app non modifica nulla del robot.
"""
import json

from shared.config import APP_DIR

# state/ sta alla radice del repo, un livello sopra app/
STATE_DIR = APP_DIR.parent / "state"
PREDICTIONS = STATE_DIR / "predictions.json"

# Impatto -> (freccia, classe .pill del design system). I COLORI vivono nel CSS
# (light/dark), qui usiamo solo le classi: niente hex fissi -> temi coerenti.
_IMPACT = {
    "positivo": ("▲", "green"),  # .pill.green -> var(--pos)
    "neutro":   ("=", "gray"),   # .pill.gray  -> grigio neutro
    "negativo": ("▼", "red"),    # .pill.red   -> var(--neg)
}


def _norm_impact(val) -> str:
    s = str(val or "").lower()
    if "positiv" in s:
        return "positivo"
    if "negativ" in s:
        return "negativo"
    return "neutro"


def _norm_conf(val) -> str:
    s = str(val or "").lower()
    if "alt" in s:
        return "alta"
    if "bass" in s:
        return "bassa"
    return "media"


def _overall_class(imp: dict) -> str:
    """Variante .card dal rail di sinistra secondo l'impatto netto:
    'green' (pos) / 'red' (neg) / '' (neutro, card liscia). Il colore è nel CSS."""
    vals = [_norm_impact((imp or {}).get(k)) for k in ("breve", "medio", "lungo")]
    pos, neg = vals.count("positivo"), vals.count("negativo")
    if pos > neg:
        return "green"
    if neg > pos:
        return "red"
    return ""


def _rel_class(score) -> str:
    """Classe .badge per la rilevanza (soglie INVARIATE: 70 critico, 50 report).
    high=critico (rosso) · mid=report (giallo) · low=info (grigio). Colori nel CSS."""
    try:
        s = int(score)
    except (TypeError, ValueError):
        s = 0
    if s >= 70:
        return "high"
    if s >= 50:
        return "mid"
    return "low"


def _load_items():
    try:
        with open(PREDICTIONS, "r", encoding="utf-8") as fh:
            return json.load(fh).get("items", [])
    except (OSError, json.JSONDecodeError):
        return []


def news_cards(limit: int = 30):
    """Card pronte per il template, ordinate per data (recente) e rilevanza."""
    items = _load_items()
    items.sort(key=lambda it: (str(it.get("data", "")), it.get("rilevanza", 0) or 0),
               reverse=True)
    cards = []
    for it in items[:limit]:
        imp = it.get("impatto") or {}
        impatti = []
        for hk, key in (("short", "breve"), ("medium", "medio"), ("long", "lungo")):
            vw = _norm_impact(imp.get(key))
            arrow, pill = _IMPACT[vw]
            impatti.append({"hk": hk, "vw": vw, "arrow": arrow, "pill": pill})
        cards.append({
            "ticker": it.get("ticker", ""),
            "titolo": it.get("titolo", ""),
            "tipo_evento": it.get("tipo_evento", ""),
            "rilevanza": it.get("rilevanza", ""),
            "rel_class": _rel_class(it.get("rilevanza")),
            "confidenza": _norm_conf(it.get("confidenza")),
            "data": str(it.get("data", ""))[:10],
            "url": it.get("url", ""),
            "impatti": impatti,
            "bordo_class": _overall_class(imp),
        })
    return cards


def latest_date() -> str:
    """Data della notizia più recente (per l'etichetta 'aggiornato al')."""
    ds = [str(it.get("data", ""))[:10] for it in _load_items() if it.get("data")]
    return max(ds) if ds else ""
