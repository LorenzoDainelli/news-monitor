"""Salvataggio di tema e lingua, poi ritorno alla pagina da cui sei partito."""
from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse

from shared import prefs

router = APIRouter()


def _safe_next(next_url: str) -> str:
    # accetto solo percorsi interni (iniziano con una sola '/'): niente redirect esterni
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return "/"


@router.post("/preferenze")
def salva_preferenze(theme: str = Form(None), lang: str = Form(None), next: str = Form("/")):
    if theme:
        prefs.set_theme(theme)
    if lang:
        prefs.set_lang(lang)
    return RedirectResponse(_safe_next(next), status_code=303)
