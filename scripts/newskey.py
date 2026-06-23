#!/usr/bin/env python3
"""Chiave di deduplica deterministica per le notizie, derivata dall'URL.

Perche' esiste: il modello inventa un campo `id` diverso a ogni run, quindi
deduplicare su `id` NON funziona (la stessa notizia rientra con un id nuovo).
Questa funzione produce invece una chiave stabile a partire dall'URL, condivisa
da `fetch_news.py` (filtro a monte) e `update_state.py` (merge dello stato).

Solo libreria standard.
"""
import re


def news_key(url: str) -> str:
    """Chiave stabile da un URL. Stringa vuota se l'URL manca.

    - URL delle news Finnhub (`...?id=<hash>`): si usa l'hash univoco.
    - Altri URL: si normalizza (no schema/www/slash finale/query/fragment).
    """
    u = (url or "").strip().lower()
    if not u:
        return ""
    m = re.search(r"[?&]id=([0-9a-z]{16,})", u)
    if m:
        return "finnhub:" + m.group(1)
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    u = u.split("#", 1)[0].split("?", 1)[0].rstrip("/")
    return u
