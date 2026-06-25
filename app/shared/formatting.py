"""Formattazione numeri all'italiana: euro e percentuali.

Esempi:
    format_eur(1234.5)  -> "€ 1.234,50"
    format_pct(2.75)    -> "2,75%"
    format_pct(20)      -> "20%"
Regola: valute in €, percentuali con %, massimo 2 decimali, virgola decimale.
"""


def format_eur(value, decimals: int = 2) -> str:
    if value is None:
        return "—"
    s = f"{float(value):,.{decimals}f}"          # stile inglese: 1,234.50
    s = s.replace(",", "§").replace(".", ",").replace("§", ".")  # -> 1.234,50
    return f"€ {s}"


def format_pct(value, decimals: int = 2) -> str:
    if value is None:
        return "—"
    s = f"{float(value):.{decimals}f}"
    if "." in s:                                  # togli zeri inutili: 20,00 -> 20
        s = s.rstrip("0").rstrip(".")
    return f"{s.replace('.', ',')}%"


def format_qty(value) -> str:
    """Quantità possedute: fino a 4 decimali, senza zeri inutili (frazioni ETF)."""
    if value is None:
        return "—"
    s = f"{float(value):.4f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s.replace(".", ",")
