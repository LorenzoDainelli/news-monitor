"""Pagina Impostazioni: inserimento delle chiavi API (salvate solo in locale).

L'app funziona senza chiavi. Inserendone una si sbloccano funzioni extra (es.
l'agente AI con la chiave Gemini). Le chiavi non vengono mai mostrate in chiaro
ne' loggate.
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse

from shared.templating import templates
from shared import settings_store as store

router = APIRouter()


@router.get("/impostazioni", response_class=HTMLResponse)
def impostazioni(request: Request, salvato: int = 0):
    voci = []
    for chiave, meta in store.KNOWN_SETTINGS.items():
        valore = store.get_setting(chiave, "")
        voci.append({
            "chiave": chiave,
            "tkey": meta["tkey"],
            "secret": meta.get("secret", False),
            "presente": bool(valore.strip()),
            "mascherato": store.masked(valore) if meta.get("secret") else valore,
        })
    return templates.TemplateResponse(request, "settings.html", {
        "active": "impostazioni",
        "voci": voci, "salvato": bool(salvato),
    })


@router.post("/impostazioni")
async def salva(request: Request):
    form = await request.form()
    for chiave in store.KNOWN_SETTINGS:
        # campo lasciato vuoto = NON cambiare (cosi' non cancelli una chiave gia' messa)
        nuovo = (form.get(chiave) or "").strip()
        if form.get(f"clear_{chiave}"):          # casella "rimuovi" spuntata
            store.set_setting(chiave, "")
        elif nuovo:
            store.set_setting(chiave, nuovo)
    return RedirectResponse("/impostazioni?salvato=1", status_code=303)
