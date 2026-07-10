"""Helper per i mini-grafici SVG (polyline) di dashboard e dettaglio posizione.

Dal HANDOFF del design: trasforma una serie numerica nei punti "x,y x,y ..."
già scalati per la viewBox dell'SVG. Nessuna dipendenza.
"""


def chart_points(series, w=560, h=132, pad=6):
    """Ritorna (points_str, is_up) per una polyline SVG.

    Dettaglio posizione: default 560×132. Trend dashboard: w=620, h=150.
    Serie vuota o con meno di 2 punti -> ("", True): il blocco resta nascosto.
    """
    if not series or len(series) < 2:
        return "", True
    lo, hi = min(series), max(series)
    span = (hi - lo) or 1
    n = len(series)
    pts = [
        f"{pad + i * (w - 2 * pad) / (n - 1):.1f},{pad + (h - 2 * pad) * (1 - (v - lo) / span):.1f}"
        for i, v in enumerate(series)
    ]
    return " ".join(pts), series[-1] >= series[0]
