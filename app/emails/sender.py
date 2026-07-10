"""Invio email tramite l'API HTTP di Resend (logica condivisa, solo stdlib).

La chiave API arriva SEMPRE dal chiamante (che la legge dall'ambiente): questo
modulo non tocca variabili d'ambiente, non stampa e non logga mai la chiave.
"""
import base64
import json
import os
import urllib.request

RESEND_ENDPOINT = "https://api.resend.com/emails"

# Lo User-Agent di default di urllib (Python-urllib/x.y) è spesso bloccato da
# Cloudflare (errore 1010): usiamo uno UA standard da browser.
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
       "AppleWebKit/537.36 (KHTML, like Gecko) "
       "Chrome/124.0.0.0 Safari/537.36")


def send(api_key: str, sender: str, to: str, subject: str, html: str,
         attachments: list[str] | None = None, timeout: int = 30) -> str:
    """Invia l'email e ritorna l'id assegnato da Resend.

    'attachments' è una lista di percorsi file. Solleva le eccezioni di urllib
    (HTTPError/URLError) o OSError sugli allegati: le gestisce il chiamante.
    """
    payload = {"from": sender, "to": [to], "subject": subject, "html": html}
    if attachments:
        payload["attachments"] = [
            {"filename": os.path.basename(p),
             "content": base64.b64encode(open(p, "rb").read()).decode("ascii")}
            for p in attachments
        ]
    request = urllib.request.Request(
        RESEND_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": _UA,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
    try:
        return json.loads(body).get("id", "(id non disponibile)")
    except json.JSONDecodeError:
        return "(risposta non JSON)"
