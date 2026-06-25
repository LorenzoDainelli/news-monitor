"""Dati di mercato: prezzi correnti e conversione in euro. Tutto GRATIS.

Fonte primaria: Yahoo Finance (lo stesso dato di yfinance) via chiamata diretta,
senza librerie pesanti. Ripiego: Stooq. Nessuna chiave API.

Regole d'oro (dal CLAUDE.md):
- MAI inventare: se un prezzo non è reperibile si segna 'non disponibile' e si
  tiene la data dell'ultimo aggiornamento riuscito.
- Robustezza: ogni titolo è gestito a sé; se una chiamata fallisce, si prosegue.
- I prezzi pubblici NON sono dati sensibili: qui non c'è nulla di personale.
"""
import csv
import io
import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

from sqlalchemy import String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.db import Base, SessionLocal
from portfolio.models import Position

UA = {"User-Agent": "Mozilla/5.0 (finanza-app personale)"}
TIMEOUT = 8
ROME_OFFSET = timedelta(hours=2)  # ~Europe/Rome (CEST), come il news-monitor

# Simboli Yahoo verificati per gli ETF europei: il ticker "semplice" non basta,
# serve il suffisso di borsa. Le azioni USA usano invece il ticker così com'è.
SYMBOL_MAP = {
    "IWDA": "IWDA.AS", "CSPX": "CSPX.L", "CNDX": "CNDX.L", "VHYL": "VHYL.L",
    "XDWH": "XDWH.DE", "NATO": "NATO.L", "NUKL": "NUKL.DE", "XDWM": "XDWM.DE",
    "GIFL": "GGRP.L", "UKRN": "UKRN.L", "HEAL": "HEAL.L",
}


class Quote(Base):
    """Ultimo prezzo noto per un ticker (cache locale)."""
    __tablename__ = "portfolio_quotes"
    ticker: Mapped[str] = mapped_column(String(30), primary_key=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)        # valuta nativa
    currency: Mapped[str] = mapped_column(String(8), default="")
    price_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="")
    ok: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[str] = mapped_column(Text, default="")
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# ----------------------------- recupero dati ------------------------------
def _yahoo_symbol(ticker: str) -> str:
    return SYMBOL_MAP.get(ticker.upper(), ticker)


def _http(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def _yahoo_quote(symbol: str):
    """(prezzo, valuta) da Yahoo. Gestisce le quotazioni in pence (GBp/GBX)."""
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/"
           f"{urllib.parse.quote(symbol)}?range=1d&interval=1d")
    meta = json.loads(_http(url))["chart"]["result"][0]["meta"]
    price = meta.get("regularMarketPrice")
    if price is None:
        raise ValueError("prezzo assente")
    cur_raw = meta.get("currency") or ""
    price = float(price)
    if cur_raw in ("GBp", "GBX"):          # Londra quota spesso in pence
        return price / 100.0, "GBP"
    if cur_raw in ("ZAc", "ILA"):          # altri casi in centesimi
        return price / 100.0, cur_raw[:-1].upper()
    return price, cur_raw.upper()


def _stooq_quote(ticker: str):
    """Ripiego: Stooq (CSV). Funziona soprattutto per i titoli USA ('aapl.us')."""
    sym = f"{ticker.lower()}.us"
    url = f"https://stooq.com/q/l/?s={urllib.parse.quote(sym)}&f=sd2t2ohlc&e=csv"
    rows = list(csv.DictReader(io.StringIO(_http(url).decode("utf-8", "replace"))))
    if not rows:
        raise ValueError("nessun dato")
    close = rows[0].get("Close")
    if not close or close in ("N/D", "0"):
        raise ValueError("nessuna chiusura")
    return float(close), "USD"


_FX_CACHE: dict[str, float] = {}


def _fx_to_eur_rate(currency: str) -> float:
    """Quante unità di 'currency' valgono 1 EUR (per dividere e ottenere gli euro)."""
    cur = (currency or "EUR").upper()
    if cur == "EUR":
        return 1.0
    if cur in _FX_CACHE:
        return _FX_CACHE[cur]
    rate, _ = _yahoo_quote(f"EUR{cur}=X")
    _FX_CACHE[cur] = rate
    return rate


# ----------------------------- aggiornamento ------------------------------
def _store(ticker, **kw):
    with SessionLocal() as db:
        q = db.get(Quote, ticker) or Quote(ticker=ticker)
        for k, v in kw.items():
            setattr(q, k, v)
        db.add(q)
        db.commit()


def _refresh_one(ticker: str) -> None:
    now = datetime.utcnow()
    try:
        price, cur = _yahoo_quote(_yahoo_symbol(ticker))
        source = "Yahoo"
    except Exception as e1:
        try:
            price, cur = _stooq_quote(ticker)
            source = "Stooq"
        except Exception:
            _store(ticker, ok=False, error=type(e1).__name__, fetched_at=now)
            return
    try:
        rate = _fx_to_eur_rate(cur)
        price_eur = round(price / rate, 4) if rate else None
    except Exception:
        price_eur = None
    _store(ticker, price=round(price, 4), currency=cur, price_eur=price_eur,
           source=source, ok=True, error="", fetched_at=now)


def refresh_all() -> int:
    """Aggiorna i prezzi di tutti i ticker del portafoglio. Ritorna quanti ok."""
    _FX_CACHE.clear()
    with SessionLocal() as db:
        tickers = [p.ticker.strip() for p in db.query(Position).all() if p.ticker.strip()]
    visti, ok = set(), 0
    for tk in tickers:
        if tk.upper() in visti:
            continue
        visti.add(tk.upper())
        _refresh_one(tk)
    with SessionLocal() as db:
        ok = db.query(Quote).filter(Quote.ok.is_(True)).count()
    return ok


# ----------------------------- lettura/cache ------------------------------
def quotes_map() -> dict:
    with SessionLocal() as db:
        return {q.ticker.upper(): q for q in db.query(Quote).all()}


def last_update():
    with SessionLocal() as db:
        rows = [q.fetched_at for q in db.query(Quote).all() if q.fetched_at]
    return max(rows) if rows else None


def is_stale(max_age_min: int = 360) -> bool:
    lu = last_update()
    if lu is None:
        return True
    return (datetime.utcnow() - lu).total_seconds() / 60.0 > max_age_min


def fmt_ts(dt) -> str | None:
    if not dt:
        return None
    return (dt + ROME_OFFSET).strftime("%d/%m %H:%M")
