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

# Stesso linguaggio visivo delle email (vedi scripts/render_email.py)
_IMPACT = {
    "positivo": ("▲", "#1a7f37", "#e6f4ea"),  # ▲ verde
    "neutro":   ("=",      "#57606a", "#eaeef2"),
    "negativo": ("▼", "#cf222e", "#ffebe9"),  # ▼ rosso
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


def _overall_color(imp: dict) -> str:
    """Colore del bordo card secondo l'impatto netto (verde/rosso/grigio)."""
    vals = [_norm_impact((imp or {}).get(k)) for k in ("breve", "medio", "lungo")]
    pos, neg = vals.count("positivo"), vals.count("negativo")
    if pos > neg:
        return "#1a7f37"
    if neg > pos:
        return "#cf222e"
    return "#8b949e"


def _rel_colors(score):
    """Sfondo/testo del badge rilevanza (allineato alle soglie: 70 critico, 50 report)."""
    try:
        s = int(score)
    except (TypeError, ValueError):
        s = 0
    if s >= 70:
        return "#ffebe9", "#cf222e"
    if s >= 50:
        return "#fff3cd", "#9a6700"
    return "#eaeef2", "#57606a"


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
            arrow, color, bg = _IMPACT[vw]
            impatti.append({"hk": hk, "vw": vw, "arrow": arrow, "color": color, "bg": bg})
        rel_bg, rel_col = _rel_colors(it.get("rilevanza"))
        cards.append({
            "ticker": it.get("ticker", ""),
            "titolo": it.get("titolo", ""),
            "tipo_evento": it.get("tipo_evento", ""),
            "rilevanza": it.get("rilevanza", ""),
            "rel_bg": rel_bg,
            "rel_col": rel_col,
            "confidenza": _norm_conf(it.get("confidenza")),
            "data": str(it.get("data", ""))[:10],
            "url": it.get("url", ""),
            "impatti": impatti,
            "bordo": _overall_color(imp),
        })
    return cards


def latest_date() -> str:
    """Data della notizia più recente (per l'etichetta 'aggiornato al')."""
    ds = [str(it.get("data", ""))[:10] for it in _load_items() if it.get("data")]
    return max(ds) if ds else ""
