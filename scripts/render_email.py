#!/usr/bin/env python3
"""Genera l'HTML dell'email da un JSON compatto (CLI per le routine cloud).

La logica di rendering vive in app/emails/render.py (design MyMoney, condiviso
con la web app): questo file è solo l'ingresso a riga di comando, con la STESSA
interfaccia di sempre. Solo libreria standard.

Uso:
    python scripts/render_email.py --data-file report.json --out out.html
"""
import argparse
import json
import os
import sys

# la logica condivisa sta nell'app (app/emails/render.py, solo stdlib)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from emails.render import build_html  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Render HTML email da JSON.")
    ap.add_argument("--data-file", required=True)
    ap.add_argument("--out", default="out.html")
    args = ap.parse_args()
    try:
        with open(args.data_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERRORE lettura {args.data_file}: {exc}", file=sys.stderr)
        return 1
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(build_html(data))
    print(f"HTML scritto in {args.out} ({len(data.get('items') or [])} voci)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
