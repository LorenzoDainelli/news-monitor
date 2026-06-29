"""Sezione Notizie (Fase 5): mostra le notizie del news-monitor nell'app.

Sola lettura del file di stato del robot; nessuna chiamata di rete qui.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from shared.templating import templates
from news import reader

router = APIRouter()


@router.get("/notizie", response_class=HTMLResponse)
def notizie(request: Request):
    return templates.TemplateResponse(request, "notizie.html", {
        "active": "notizie",
        "cards": reader.news_cards(limit=30),
        "aggiornato": reader.latest_date(),
    })
