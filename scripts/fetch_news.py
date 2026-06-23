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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from newskey import news_key  # noqa: E402

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
    ap.add_argument("--seen-file", default="",
                    help="Path a state/seen.json: scarta le notizie con URL gia' "
                         "inviato e fornisce 'recent_seen' per la dedup di evento")
    ap.add_argument("--recent-days", type=int, default=4,
                    help="Giorni di storico in 'recent_seen' (dedup di evento)")
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

    # Stato gia' inviato: chiavi-URL da filtrare a monte + elenco compatto
    # 'recent_seen' (ticker+titolo) per far riconoscere al modello i DOPPIONI di
    # evento (stesso fatto da fonte/URL diverso).
    seen_keys = set()
    recent_seen = []
    if args.seen_file:
        try:
            with open(args.seen_file, "r", encoding="utf-8") as fh:
                seen_items = json.load(fh).get("items", [])
        except (OSError, json.JSONDecodeError):
            seen_items = []
        rec_cutoff = (now - timedelta(days=args.recent_days)).isoformat()
        for s in seen_items:
            k = news_key(s.get("url", ""))
            if k:
                seen_keys.add(k)
            d = s.get("data_invio", "")
            if (not d) or d[:19] >= rec_cutoff[:19]:
                recent_seen.append({
                    "ticker": s.get("ticker", ""),
                    "titolo": s.get("titolo", ""),
                    "data": (d[:10] if d else ""),
                })

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    by_url = {}
    errors = []
    n_filtrate = 0

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
            if news_key(url) in seen_keys:  # gia' inviata: non riproporla al modello
                n_filtrate += 1
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
                if news_key(it.get("url", "")) in seen_keys:  # gia' inviata
                    n_filtrate += 1
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
        "n_filtrate": n_filtrate,  # notizie scartate perche' gia' inviate (URL noto)
        "items": sorted(by_url.values(), key=lambda x: x["date"], reverse=True),
        "macro": macro,
        "recent_seen": recent_seen,  # inviate negli ultimi giorni: per dedup di EVENTO
    }
    print(json.dumps(out, ensure_ascii=False))
    if errors:
        print("AVVISI (titoli saltati): " + "; ".join(errors), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
