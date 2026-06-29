"""Pagina Impostazioni: inserimento delle chiavi API (salvate solo in locale).

L'app funziona senza chiavi. Inserendone una si sbloccano funzioni extra (es.
l'agente AI con la chiave Gemini). Le chiavi non vengono mai mostrate in chiaro
ne' loggate.
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse

from shared.templating import templates
from shared import settings_store as store
from shared import ai

router = APIRouter()


@router.get("/impostazioni", response_class=HTMLResponse)
def impostazioni(request: Request, salvato: int = 0, ai_test: str = ""):
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
        "ai_configured": ai.is_configured(),
        "ai_model": ai.get_model(),
        "ai_mode": ai.get_mode(),
        "ai_test": ai_test,
        "MODES": ai.MODES,
    })


@router.post("/impostazioni/ai")
def salva_ai(modello: str = Form(""), modalita: str = Form("")):
    ai.set_model(modello)
    ai.set_mode(modalita)
    return RedirectResponse("/impostazioni?salvato=1", status_code=303)


def _esito_test(ok: bool, detail: str) -> str:
    """Traduce l'esito grezzo di test_connection in un codice per l'interfaccia."""
    if ok:
        return "ok"
    d = (detail or "").lower()
    if d == "no_key":
        return "nokey"
    if "401" in d or "403" in d:
        return "badkey"      # chiave non valida
    if "429" in d:
        return "rate"        # limite di richieste raggiunto (free tier)
    if d == "rete":
        return "net"         # nessuna connessione
    return "err"


@router.post("/impostazioni/ai/test")
def prova_ai():
    ok, detail = ai.test_connection()
    return RedirectResponse(f"/impostazioni?ai_test={_esito_test(ok, detail)}", status_code=303)


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
