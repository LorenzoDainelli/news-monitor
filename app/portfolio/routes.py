"""Pagine del portafoglio: elenco posizioni, aggiungi/modifica/elimina, PAC.

Tutto modificabile dall'interfaccia, MAI da codice (come da requisiti).
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse

from shared.db import SessionLocal
from shared.templating import templates
from shared.parsing import to_float, to_date
from portfolio.models import Position, TIPO_ETF, TIPO_AZIONE
from portfolio import service

router = APIRouter()


@router.get("/portafoglio", response_class=HTMLResponse)
def elenco(request: Request):
    return templates.TemplateResponse(request, "portfolio_positions.html", {
        "active": "portafoglio",
        "posizioni": service.lista_posizioni(),
        "riepilogo": service.riepilogo(),
    })


@router.get("/portafoglio/nuovo", response_class=HTMLResponse)
def form_nuovo(request: Request):
    return templates.TemplateResponse(request, "portfolio_form.html", {
        "active": "portafoglio",
        "p": None, "tipi": [TIPO_ETF, TIPO_AZIONE],
    })


@router.get("/portafoglio/{pos_id}/modifica", response_class=HTMLResponse)
def form_modifica(request: Request, pos_id: int):
    with SessionLocal() as db:
        p = db.get(Position, pos_id)
        if p is None:
            return RedirectResponse("/portafoglio", status_code=303)
        return templates.TemplateResponse(request, "portfolio_form.html", {
            "active": "portafoglio",
            "p": p, "tipi": [TIPO_ETF, TIPO_AZIONE],
        })


@router.post("/portafoglio/salva")
def salva(
    pos_id: str = Form(""),
    nome: str = Form(...),
    tipo: str = Form(TIPO_AZIONE),
    categoria: str = Form(""),
    ticker: str = Form(""),
    isin: str = Form(""),
    pct_target: str = Form("0"),
    importo_fisso: str = Form(""),
    quantita: str = Form(""),
    valore_posseduto: str = Form(""),
    data_ultimo_acquisto: str = Form(""),
    note: str = Form(""),
):
    dati = dict(
        nome=nome.strip(),
        tipo=tipo if tipo in (TIPO_ETF, TIPO_AZIONE) else TIPO_AZIONE,
        categoria=categoria.strip(),
        ticker=ticker.strip().upper(),
        isin=isin.strip().upper(),
        pct_target=to_float(pct_target, 0.0) or 0.0,
        importo_fisso=to_float(importo_fisso, None),
        quantita=to_float(quantita, None),
        valore_posseduto=to_float(valore_posseduto, None),
        data_ultimo_acquisto=to_date(data_ultimo_acquisto),
        note=note.strip(),
    )
    with SessionLocal() as db:
        if pos_id.strip():                      # modifica di una posizione esistente
            p = db.get(Position, int(pos_id))
            if p:
                for k, v in dati.items():
                    setattr(p, k, v)
        else:                                   # nuova posizione, in fondo all'elenco
            ultimo = db.query(Position).order_by(Position.ordine.desc()).first()
            dati["ordine"] = (ultimo.ordine + 1) if ultimo else 0
            db.add(Position(**dati))
        db.commit()
    return RedirectResponse("/portafoglio", status_code=303)


@router.post("/portafoglio/{pos_id}/elimina")
def elimina(pos_id: int):
    with SessionLocal() as db:
        p = db.get(Position, pos_id)
        if p:
            db.delete(p)
            db.commit()
    return RedirectResponse("/portafoglio", status_code=303)


@router.get("/pac", response_class=HTMLResponse)
def pac(request: Request, importo: str = "500"):
    importo_val = to_float(importo, 500.0) or 0.0
    return templates.TemplateResponse(request, "pac.html", {
        "active": "pac",
        "r": service.calcola_pac(importo_val),
        "importo_input": importo,
    })
