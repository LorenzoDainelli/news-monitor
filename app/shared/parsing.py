"""Lettura tollerante dei numeri/date inseriti nei moduli.

Accetta sia '2,75' sia '2.75', con o senza simbolo €, cosi' non sbagli a digitare.
"""
from datetime import date, datetime


def to_float(value, default=None):
    if value is None:
        return default
    s = str(value).strip().replace(" ", "").replace("€", "")
    if not s:
        return default
    if "," in s and "." in s:        # es. 1.234,56 -> 1234.56
        s = s.replace(".", "").replace(",", ".")
    else:                            # es. 2,75 -> 2.75
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return default


def to_date(value):
    s = (value or "").strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s)          # i campi <input type=date> usano YYYY-MM-DD
    except ValueError:
        return None


def to_datetime(value):
    s = (value or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)  # <input type=datetime-local> = YYYY-MM-DDTHH:MM
        except ValueError:
            pass
    return None
