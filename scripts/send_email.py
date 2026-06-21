#!/usr/bin/env python3
"""Invia un'email tramite l'API HTTP di Resend.

Uso:
    python scripts/send_email.py \
        --to dest@example.com \
        --from "Monitor Titoli <onboarding@resend.dev>" \
        --subject "Oggetto" \
        --html-file out.html \
        [--attachment report.pdf]

La chiave API viene letta SOLO dalla variabile d'ambiente RESEND_API_KEY e non
viene mai stampata. Esce con codice 0 in caso di successo, 1 in caso di errore.
Usa solo la libreria standard: nessuna dipendenza da installare.
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

RESEND_ENDPOINT = "https://api.resend.com/emails"


def main() -> int:
    parser = argparse.ArgumentParser(description="Invia email via Resend.")
    parser.add_argument("--to", required=True, help="Destinatario")
    parser.add_argument("--from", dest="sender", required=True,
                        help="Mittente, es. 'Nome <indirizzo@dominio>'")
    parser.add_argument("--subject", required=True, help="Oggetto")
    parser.add_argument("--html-file", required=True, help="File HTML con il corpo")
    parser.add_argument("--attachment", action="append", default=[],
                        help="Percorso allegato (ripetibile)")
    args = parser.parse_args()

    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("ERRORE: variabile d'ambiente RESEND_API_KEY non impostata.",
              file=sys.stderr)
        return 1

    try:
        with open(args.html_file, "r", encoding="utf-8") as fh:
            html = fh.read()
    except OSError as exc:
        print(f"ERRORE: impossibile leggere {args.html_file}: {exc}", file=sys.stderr)
        return 1

    payload = {
        "from": args.sender,
        "to": [args.to],
        "subject": args.subject,
        "html": html,
    }

    attachments = []
    for path in args.attachment:
        try:
            with open(path, "rb") as fh:
                content = base64.b64encode(fh.read()).decode("ascii")
        except OSError as exc:
            print(f"ERRORE: impossibile leggere l'allegato {path}: {exc}",
                  file=sys.stderr)
            return 1
        attachments.append({"filename": os.path.basename(path), "content": content})
    if attachments:
        payload["attachments"] = attachments

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        RESEND_ENDPOINT,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            # Lo User-Agent di default di urllib (Python-urllib/x.y) è spesso
            # bloccato da Cloudflare (errore 1010). Usiamo uno UA standard.
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"ERRORE HTTP {exc.code} da Resend: {detail}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"ERRORE di rete contattando Resend: {exc.reason}", file=sys.stderr)
        return 1

    try:
        email_id = json.loads(body).get("id", "(id non disponibile)")
    except json.JSONDecodeError:
        email_id = "(risposta non JSON)"
    print(f"Email inviata. id={email_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
