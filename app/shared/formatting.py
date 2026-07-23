"""Formattazione numeri all'italiana: euro e percentuali.

Esempi:
    format_eur(1234.5)  -> "€ 1.234,50"
    format_pct(2.75)    -> "2,75%"
    format_pct(20)      -> "20%"
Regola: valute in €, percentuali con %, massimo 2 decimali, virgola decimale.
"""
import re

from markupsafe import Markup, escape


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


def format_compact(value) -> str:
    """Numeri grandi in forma compatta: 12,3 mld / 456 mln / 7,8 k."""
    if value is None:
        return "—"
    v = float(value)
    for div, suf in ((1e12, "T"), (1e9, "mld"), (1e6, "mln"), (1e3, "k")):
        if abs(v) >= div:
            return f"{v / div:.1f}".replace(".", ",") + f" {suf}"
    return f"{v:.0f}"


def format_qty(value) -> str:
    """Quantità possedute: fino a 4 decimali, senza zeri inutili (frazioni ETF)."""
    if value is None:
        return "—"
    s = f"{float(value):.4f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s.replace(".", ",")


# --- testo dell'AI: paragrafi + numeri in evidenza -------------------------
# Cifre da mettere in risalto: importi (1.234,56€ / €1.234,56) e percentuali
# (+12,3% / -4%). Servono a "dare appigli" all'occhio mentre si legge.
_RE_CIFRA = re.compile(
    r"([+-]?\d[\d. \s]*(?:,\d+)?\s*(?:€|%)|€\s*[+-]?\d[\d. \s]*(?:,\d+)?)")


def format_ai_text(testo) -> Markup:
    """Trasforma il testo dell'AI in paragrafi HTML con i numeri evidenziati.

    Il testo NON viene riscritto: si spezza sui capoversi e si avvolgono le
    cifre in <b>. Tutto è prima passato dall'escape, quindi eventuale HTML nel
    testo resta innocuo."""
    grezzo = (testo or "").strip()
    if not grezzo:
        return Markup("")
    blocchi = [b.strip() for b in re.split(r"\n\s*\n", grezzo) if b.strip()]
    if len(blocchi) == 1:                      # nessuna riga vuota: vado a capo singolo
        blocchi = [b.strip() for b in grezzo.splitlines() if b.strip()]
    out = []
    for b in blocchi:
        sicuro = str(escape(b)).replace("\n", " ")
        sicuro = _RE_CIFRA.sub(r'<b class="ai-cifra">\1</b>', sicuro)
        out.append(f"<p>{sicuro}</p>")
    return Markup("".join(out))
