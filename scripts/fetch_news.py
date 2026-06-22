#!/usr/bin/env python3
"""Scarica le notizie recenti dei titoli da Finnhub e stampa un digest COMPATTO.

Scopo: far entrare nel contesto del modello UN solo blocco piccolo invece di
decine di ricerche web (che fanno esplodere i token). Lo script fa tutte le
chiamate HTTP; il modello legge solo il JSON finale, già ridotto e deduplicato.

Uso:
    python scripts/fetch_news.py --tickers AAPL,MSFT,NVDA [--from-hours 36] \
        [--max-per-ticker 5] [--summary-chars 200] [--no-general]

Legge FINNHUB_API_KEY dalla variabile d'ambiente (non la stampa mai).
Stampa su stdout un JSON compatto. Solo libreria standard, nessuna dipendenza.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

COMPANY_NEWS = "https://finnhub.io/api/v1/company-news"
GENERAL_NEWS = "https://finnhub.io/api/v1/news"


def _get(url: str):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "monitor-titoli/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _trim(text: str, n: int) -> str:
    text = (text or "").strip().replace("\n", " ")
    return text[:n].rstrip() + "…" if len(text) > n else text


def main() -> int:
    ap = argparse.ArgumentParser(description="Digest notizie da Finnhub.")
    ap.add_argument("--tickers", required=True, help="Ticker separati da virgola")
    ap.add_argument("--from-hours", type=int, default=36)
    ap.add_argument("--max-per-ticker", type=int, default=3)
    ap.add_argument("--summary-chars", type=int, default=120)
    ap.add_argument("--no-general", action="store_true",
                    help="Salta le notizie macro generali")
    args = ap.parse_args()

    key = os.environ.get("FINNHUB_API_KEY")
    if not key:
        print("ERRORE: variabile d'ambiente FINNHUB_API_KEY non impostata.",
              file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc)
    frm = (now - timedelta(hours=args.from_hours)).date().isoformat()
    to = now.date().isoformat()
    cutoff = (now - timedelta(hours=args.from_hours)).timestamp()

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    by_url = {}
    errors = []

    for tk in tickers:
        query = urllib.parse.urlencode({"symbol": tk, "from": frm, "to": to, "token": key})
        try:
            data = _get(f"{COMPANY_NEWS}?{query}")
        except urllib.error.HTTPError as exc:
            errors.append(f"{tk}: HTTP {exc.code}")
            continue
        except Exception as exc:  # rete/timeout/parse: salta il titolo, prosegui
            errors.append(f"{tk}: {exc}")
            continue
        if not isinstance(data, list):
            continue

        kept = 0
        for it in sorted(data, key=lambda x: x.get("datetime", 0), reverse=True):
            ts = it.get("datetime", 0)
            if ts and ts < cutoff:
                continue
            url = it.get("url", "")
            if not url:
                continue
            if url in by_url:  # stessa notizia su piu' titoli: unisci i ticker
                if tk not in by_url[url]["tickers"]:
                    by_url[url]["tickers"].append(tk)
                continue
            by_url[url] = {
                "tickers": [tk],
                "title": (it.get("headline") or "").strip(),
                "source": it.get("source", ""),
                "date": datetime.fromtimestamp(ts, timezone.utc).isoformat() if ts else "",
                "url": url,
                "summary": _trim(it.get("summary", ""), args.summary_chars),
            }
            kept += 1
            if kept >= args.max_per_ticker:
                break

    macro = []
    if not args.no_general:
        try:
            gdata = _get(f"{GENERAL_NEWS}?{urllib.parse.urlencode({'category': 'general', 'token': key})}")
            for it in sorted(gdata, key=lambda x: x.get("datetime", 0), reverse=True)[:8]:
                ts = it.get("datetime", 0)
                if ts and ts < cutoff:
                    continue
                macro.append({
                    "title": (it.get("headline") or "").strip(),
                    "source": it.get("source", ""),
                    "date": datetime.fromtimestamp(ts, timezone.utc).isoformat() if ts else "",
                    "url": it.get("url", ""),
                    "summary": _trim(it.get("summary", ""), args.summary_chars),
                })
        except Exception as exc:
            errors.append(f"general: {exc}")

    out = {
        "generated_at": now.isoformat(),
        "from": frm,
        "to": to,
        "n_items": len(by_url),
        "items": sorted(by_url.values(), key=lambda x: x["date"], reverse=True),
        "macro": macro,
    }
    print(json.dumps(out, ensure_ascii=False))
    if errors:
        print("AVVISI (titoli saltati): " + "; ".join(errors), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
