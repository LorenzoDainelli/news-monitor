#!/usr/bin/env python3
"""Aggiorna i file di stato da un JSON compatto (così il modello non scrive
Python inline a ogni run). Deduplica e fa pruning. Solo libreria standard.

Uso:
    python scripts/update_state.py --data-file state_update.json [--prune-days 30]

Le due finestre di conservazione sono DIVERSE e di proposito:
- `seen.json` serve solo a non rimandare doppioni: invecchia bene, 30 giorni.
- `predictions.json` e' la base di prove per la calibrazione (verificare a
  posteriori se l'impatto stimato ci ha preso): NON si pota, altrimenti il dato
  sparisce prima ancora dell'orizzonte che dichiara (il 'medio' e' ~3 mesi).

Struttura attesa del JSON:
{
  "seen_add":        [{"id":"...","ticker":"...","url":"...","data_invio":"ISO"}],
  "predictions_add": [{"id":"...","ticker":"...","data":"ISO","tipo_evento":"...",
                       "impatto":{...},"confidenza":"...","rilevanza":80,
                       "titolo":"...","url":"..."}],
  "runlog": {"ts":"ISO","routine":"report","titoli_cercati":27,"notizie_trovate":56,
             "notizie_inviate":5,"email_inviata":true,"note":"..."}
}
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from newskey import news_key  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "state")
SEEN = os.path.join(ROOT, "seen.json")
PRED = os.path.join(ROOT, "predictions.json")
RUNLOG = os.path.join(ROOT, "runlog.ndjson")


def load_items(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh).get("items", [])
    except (OSError, json.JSONDecodeError):
        return []


def save_items(path, items):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"items": items}, fh, ensure_ascii=False, indent=2)


def _date_of(item, *keys):
    for k in keys:
        v = item.get(k)
        if v:
            return v
    return ""


def prune(items, days, *date_keys):
    if not days:
        return items
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    kept = []
    for it in items:
        d = _date_of(it, *date_keys)
        if not d or d >= cutoff:  # tieni se senza data o piu' recente del cutoff
            kept.append(it)
    return kept


def _dedup_key(it):
    """Chiave robusta: derivata dall'URL (stessa notizia = stesso URL, anche se il
    modello cambia l'`id` a ogni run). Fallback sull'`id` solo se manca l'URL."""
    k = news_key(it.get("url", ""))
    if k:
        return k
    rid = str(it.get("id") or "").strip().lower()
    return ("id:" + rid) if rid else ""


def merge(existing, additions):
    seen_keys = {_dedup_key(it) for it in existing}
    seen_keys.discard("")
    for it in additions or []:
        k = _dedup_key(it)
        if k and k in seen_keys:
            continue
        existing.append(it)
        if k:
            seen_keys.add(k)
    return existing


def main() -> int:
    ap = argparse.ArgumentParser(description="Aggiorna lo stato da JSON.")
    ap.add_argument("--data-file", required=True)
    ap.add_argument("--prune-days", type=int, default=30,
                    help="finestra di seen.json in giorni (0 = non potare)")
    ap.add_argument("--prune-days-pred", type=int, default=0,
                    help="finestra di predictions.json (0 = MAI: e' lo storico "
                         "su cui si calibra, non va buttato)")
    args = ap.parse_args()

    try:
        with open(args.data_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERRORE lettura {args.data_file}: {exc}", file=sys.stderr)
        return 1

    seen = merge(load_items(SEEN), data.get("seen_add"))
    seen = prune(seen, args.prune_days, "data_invio")
    save_items(SEEN, seen)

    pred = merge(load_items(PRED), data.get("predictions_add"))
    pred = prune(pred, args.prune_days_pred, "data")   # 0 = si tiene tutto
    save_items(PRED, pred)

    if data.get("runlog"):
        with open(RUNLOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(data["runlog"], ensure_ascii=False) + "\n")

    print(f"Stato aggiornato: seen={len(seen)} predictions={len(pred)} "
          f"(+{len(data.get('seen_add') or [])} seen, +{len(data.get('predictions_add') or [])} pred)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
