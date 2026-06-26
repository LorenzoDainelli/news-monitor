"""Pagine delle finanze: panoramica, movimenti, portafogli, categorie."""
from datetime import datetime

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from shared.templating import templates
from shared.parsing import to_float, to_datetime
from finance import service
from finance.models import TIPO_ENTRATA, TIPO_USCITA, TIPO_TRASFERIMENTO, TIPI_WALLET

router = APIRouter()


def _oggi_local():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M")


# ------------------------------ panoramica ------------------------------
@router.get("/finanze", response_class=HTMLResponse)
def panoramica(request: Request):
    now = datetime.utcnow()
    return templates.TemplateResponse(request, "finance_overview.html", {
        "active": "finanze",
        "saldi": service.saldi(),
        "riep": service.riepilogo_mese(now.year, now.month),
        "movimenti": service.lista_movimenti(limit=8),
        "wallets": service.wallets(),
        "categorie": service.categorie(),
        "tipi": (TIPO_ENTRATA, TIPO_USCITA, TIPO_TRASFERIMENTO),
        "oggi": _oggi_local(),
    })


# ------------------------------ movimenti ------------------------------
@router.get("/finanze/movimenti", response_class=HTMLResponse)
def movimenti(request: Request):
    now = datetime.utcnow()
    return templates.TemplateResponse(request, "finance_transactions.html", {
        "active": "finanze",
        "movimenti": service.lista_movimenti(limit=300),
        "wallets": service.wallets(),
        "categorie": service.categorie(),
        "tipi": (TIPO_ENTRATA, TIPO_USCITA, TIPO_TRASFERIMENTO),
        "oggi": _oggi_local(),
    })


@router.post("/finanze/movimenti/salva")
def salva_movimento(
    tipo: str = Form(...),
    data: str = Form(""),
    importo: str = Form("0"),
    wallet_id: int = Form(...),
    wallet_to_id: str = Form(""),
    categoria: str = Form(""),
    metodo: str = Form(""),
    descrizione: str = Form(""),
    next: str = Form("/finanze"),
):
    if tipo in (TIPO_ENTRATA, TIPO_USCITA, TIPO_TRASFERIMENTO):
        wto = int(wallet_to_id) if (wallet_to_id or "").strip().isdigit() else None
        service.crea_movimento(
            tipo=tipo, data=to_datetime(data), importo=to_float(importo, 0.0) or 0.0,
            wallet_id=wallet_id, wallet_to_id=wto, categoria_nome=categoria,
            metodo=metodo, descrizione=descrizione)
    dest = next if next.startswith("/finanze") else "/finanze"
    # autoplay della scena sul portafoglio toccato (il board legge ?play=&dir=)
    if tipo in (TIPO_ENTRATA, TIPO_USCITA):
        d = "in" if tipo == TIPO_ENTRATA else "out"
        sep = "&" if "?" in dest else "?"
        dest = f"{dest}{sep}play={wallet_id}&dir={d}"
    return RedirectResponse(dest, status_code=303)


@router.post("/finanze/movimenti/{tid}/elimina")
def elimina_movimento(tid: int, next: str = Form("/finanze")):
    service.elimina_movimento(tid)
    dest = next if next.startswith("/finanze") else "/finanze"
    return RedirectResponse(dest, status_code=303)


# ------------------------------ portafogli ------------------------------
@router.get("/finanze/portafogli", response_class=HTMLResponse)
def portafogli(request: Request):
    return templates.TemplateResponse(request, "finance_wallets.html", {
        "active": "finanze", "saldi": service.saldi(), "tipi": TIPI_WALLET, "edit": None,
    })


@router.get("/finanze/portafogli/{wid}/modifica", response_class=HTMLResponse)
def portafoglio_modifica(request: Request, wid: int):
    w = service.get_wallet(wid)
    if not w:
        return RedirectResponse("/finanze/portafogli", status_code=303)
    return templates.TemplateResponse(request, "finance_wallets.html", {
        "active": "finanze", "saldi": service.saldi(), "tipi": TIPI_WALLET, "edit": w,
    })


@router.post("/finanze/portafogli/salva")
def salva_portafoglio(wid: str = Form(""), nome: str = Form(...), tipo: str = Form("altro"),
                      saldo_iniziale: str = Form("0"), note: str = Form("")):
    si = to_float(saldo_iniziale, 0.0) or 0.0
    tipo = tipo if tipo in TIPI_WALLET else "altro"
    if wid.strip().isdigit():
        service.aggiorna_wallet(int(wid), nome, tipo, si, note)
    else:
        service.crea_wallet(nome, tipo, si, note)
    return RedirectResponse("/finanze/portafogli", status_code=303)


@router.post("/finanze/portafogli/{wid}/elimina")
def elimina_portafoglio(wid: int):
    service.elimina_wallet(wid)
    return RedirectResponse("/finanze/portafogli", status_code=303)


# ------------------------------ categorie ------------------------------
@router.get("/finanze/categorie", response_class=HTMLResponse)
def categorie(request: Request):
    return templates.TemplateResponse(request, "finance_categories.html", {
        "active": "finanze", "categorie": service.categorie(),
    })


@router.post("/finanze/categorie/{cid}/rinomina")
def rinomina_categoria(cid: int, nome: str = Form(...)):
    if nome.strip():
        service.rinomina_categoria(cid, nome)
    return RedirectResponse("/finanze/categorie", status_code=303)


@router.post("/finanze/categorie/{cid}/unisci")
def unisci_categoria(cid: int, a_id: str = Form("")):
    if a_id.strip().isdigit():
        service.unisci_categorie(cid, int(a_id))
    return RedirectResponse("/finanze/categorie", status_code=303)


@router.post("/finanze/categorie/{cid}/elimina")
def elimina_categoria(cid: int):
    service.elimina_categoria(cid)
    return RedirectResponse("/finanze/categorie", status_code=303)
