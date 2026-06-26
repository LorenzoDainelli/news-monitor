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
import http.cookiejar
import io
import json
import threading
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


# =========================================================================
#  FONDAMENTALI: holdings degli ETF, settori, dati di fondo, dividend yield.
#  Yahoo richiede un "crumb" (token) + cookie per questi dati: lo gestiamo qui.
#  Le holdings GRATIS sono le Top 10: lo segnaliamo come elenco PARZIALE.
# =========================================================================
class Fundamentals(Base):
    """Cache dei dati di fondo/holdings per un ticker (JSON normalizzato)."""
    __tablename__ = "portfolio_fundamentals"
    ticker: Mapped[str] = mapped_column(String(30), primary_key=True)
    kind: Mapped[str] = mapped_column(String(10), default="")     # etf | stock
    data: Mapped[str] = mapped_column(Text, default="")           # JSON
    ok: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[str] = mapped_column(Text, default="")
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


_session_lock = threading.Lock()
_opener = None
_crumb = None


def _ensure_session():
    global _opener, _crumb
    if _opener and _crumb:
        return
    with _session_lock:
        if _opener and _crumb:
            return
        cj = http.cookiejar.CookieJar()
        op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        try:
            op.open(urllib.request.Request("https://fc.yahoo.com/", headers=UA), timeout=TIMEOUT)
        except Exception:
            pass  # serve solo a piazzare i cookie; spesso risponde 404
        crumb = op.open(
            urllib.request.Request("https://query2.finance.yahoo.com/v1/test/getcrumb", headers=UA),
            timeout=TIMEOUT).read().decode().strip()
        if not crumb:
            raise ValueError("crumb vuoto")
        _opener, _crumb = op, crumb


def _quote_summary(symbol: str, modules: str) -> dict:
    _ensure_session()
    url = (f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/"
           f"{urllib.parse.quote(symbol)}?modules={urllib.parse.quote(modules)}"
           f"&crumb={urllib.parse.quote(_crumb)}")
    raw = _opener.open(urllib.request.Request(url, headers=UA), timeout=TIMEOUT).read()
    res = json.loads(raw).get("quoteSummary", {}).get("result")
    if not res:
        raise ValueError("nessun risultato")
    return res[0]


def _rawv(x):
    return x.get("raw") if isinstance(x, dict) else x


def _normalize(r: dict) -> dict:
    price = r.get("price", {}) or {}
    sd = r.get("summaryDetail", {}) or {}
    fp = r.get("fundProfile", {}) or {}
    ap = r.get("assetProfile", {}) or {}
    th = r.get("topHoldings", {}) or {}
    fees = fp.get("feesExpensesInvestment", {}) or {}
    holdings = [{"symbol": h.get("symbol"), "name": h.get("holdingName"),
                 "weight": round((_rawv(h.get("holdingPercent")) or 0) * 100, 2)}
                for h in th.get("holdings", []) if _rawv(h.get("holdingPercent"))]
    sectors = []
    for s in th.get("sectorWeightings", []) or []:
        for k, v in s.items():
            w = _rawv(v)
            if w:
                sectors.append({"name": k, "weight": round(w * 100, 2)})
    return {
        "name": price.get("longName") or price.get("shortName"),
        "currency": price.get("currency"),
        "quote_type": price.get("quoteType"),
        "category": fp.get("categoryName"),
        "total_assets": _rawv(sd.get("totalAssets")),
        "expense_ratio": _rawv(fees.get("annualReportExpenseRatio")),
        "div_yield": _rawv(sd.get("yield")) or _rawv(sd.get("dividendYield")) or _rawv(sd.get("trailingAnnualDividendYield")),
        "beta": _rawv(sd.get("beta")) or _rawv(sd.get("beta3Year")),
        "sector": ap.get("sector"),
        "industry": ap.get("industry"),
        "country": ap.get("country"),
        "holdings": holdings,
        "holdings_count": _rawv(th.get("holdingsCount")) if th.get("holdingsCount") else None,
        "sectors": sectors,
    }


def _store_fund(ticker, **kw):
    key = ticker.upper()
    with SessionLocal() as db:
        f = db.get(Fundamentals, key) or Fundamentals(ticker=key)
        for k, v in kw.items():
            setattr(f, k, v)
        db.add(f)
        db.commit()


MODULES = "topHoldings,fundProfile,summaryDetail,assetProfile,price,quoteType"


def fetch_fundamentals(ticker: str, tipo: str = "") -> None:
    now = datetime.utcnow()
    try:
        r = _quote_summary(_yahoo_symbol(ticker), MODULES)
        data = _normalize(r)
        kind = "etf" if (data.get("holdings") or tipo == "ETF") else "stock"
        _store_fund(ticker, kind=kind, data=json.dumps(data), ok=True, error="", fetched_at=now)
    except Exception as e:
        _store_fund(ticker, ok=False, error=type(e).__name__, fetched_at=now)


def get_fundamentals(ticker: str, max_age_h: int = 24, tipo: str = "") -> dict | None:
    """Ritorna i fondamentali dalla cache; li scarica se mancanti o vecchi.
    Ritorna None se non reperibili (cosi' la pagina mostra 'non disponibile')."""
    key = (ticker or "").strip().upper()
    if not key:
        return None
    with SessionLocal() as db:
        f = db.get(Fundamentals, key)
    stale = (f is None) or (f.fetched_at is None) or \
            ((datetime.utcnow() - f.fetched_at).total_seconds() / 3600.0 > max_age_h)
    if stale:
        fetch_fundamentals(ticker, tipo)
        with SessionLocal() as db:
            f = db.get(Fundamentals, key)
    if f and f.ok and f.data:
        d = json.loads(f.data)
        d["_fetched"] = fmt_ts(f.fetched_at)
        return d
    return None


def refresh_all_fundamentals(max_age_h: int = 24) -> None:
    """Scarica/aggiorna i fondamentali di tutti i ticker (per look-through e rischio)."""
    with SessionLocal() as db:
        positions = [(p.ticker.strip(), p.tipo) for p in db.query(Position).all()
                     if (p.ticker or "").strip()]
    seen = set()
    for tk, tipo in positions:
        if tk.upper() in seen:
            continue
        seen.add(tk.upper())
        try:
            get_fundamentals(tk, max_age_h=max_age_h, tipo=tipo)
        except Exception:
            pass


def history_closes(symbol: str, rng: str = "1y", interval: str = "1wk") -> list:
    """Serie storica delle chiusure (per le metriche di rischio). [] se non c'e'."""
    try:
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/"
               f"{urllib.parse.quote(symbol)}?range={rng}&interval={interval}")
        res = json.loads(_http(url))["chart"]["result"][0]
        closes = res["indicators"]["quote"][0]["close"]
        return [c for c in closes if c is not None]
    except Exception:
        return []
