#!/usr/bin/env python3
"""Invia un'email tramite l'API HTTP di Resend (CLI per le routine cloud).

La logica d'invio vive in app/emails/sender.py (condivisa): questo file è solo
l'ingresso a riga di comando, con la STESSA interfaccia di sempre.

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
import os
import sys
import urllib.error

# la logica condivisa sta nell'app (app/emails/sender.py, solo stdlib)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from emails.sender import send  # noqa: E402


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

    try:
        email_id = send(api_key, args.sender, args.to, args.subject, html,
                        attachments=args.attachment)
    except OSError as exc:
        # copre anche gli allegati illeggibili
        if isinstance(exc, urllib.error.HTTPError):
            detail = exc.read().decode("utf-8", errors="replace")
            print(f"ERRORE HTTP {exc.code} da Resend: {detail}", file=sys.stderr)
        elif isinstance(exc, urllib.error.URLError):
            print(f"ERRORE di rete contattando Resend: {exc.reason}", file=sys.stderr)
        else:
            print(f"ERRORE: {exc}", file=sys.stderr)
        return 1

    print(f"Email inviata. id={email_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
