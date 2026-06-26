"""Pagine del portafoglio: elenco posizioni, aggiungi/modifica/elimina, PAC.

Tutto modificabile dall'interfaccia, MAI da codice (come da requisiti).
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse

from shared.db import SessionLocal
from shared.templating import templates
from shared.parsing import to_float, to_date
from portfolio.models import Position, TIPO_ETF, TIPO_AZIONE
from portfolio import service, market, analytics

router = APIRouter()


@router.get("/analisi", response_class=HTMLResponse)
def analisi(request: Request):
    return templates.TemplateResponse(request, "analisi.html", {
        "active": "analisi",
        "lt": analytics.look_through(),
        "risk": analytics.get_cached_risk(),
    })


@router.post("/analisi/rischio")
def calcola_rischio():
    analytics.compute_risk()
    return RedirectResponse("/analisi", status_code=303)


@router.get("/portafoglio", response_class=HTMLResponse)
def elenco(request: Request):
    return templates.TemplateResponse(request, "portfolio_positions.html", {
        "active": "portafoglio",
        "vista": service.vista_portafoglio(),
        "riepilogo": service.riepilogo(),
    })


@router.post("/portafoglio/aggiorna")
def aggiorna_prezzi():
    market.refresh_all()
    return RedirectResponse("/portafoglio", status_code=303)


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


@router.get("/portafoglio/{pos_id}/holdings", response_class=HTMLResponse)
def holdings_fragment(request: Request, pos_id: int):
    """Frammento HTML con le holdings dell'ETF (per la tendina cliccabile)."""
    with SessionLocal() as db:
        p = db.get(Position, pos_id)
    fund = None
    if p and (p.ticker or "").strip():
        fund = market.get_fundamentals(p.ticker, tipo=p.tipo)
    return templates.TemplateResponse(request, "portfolio_holdings_fragment.html", {"fund": fund})


@router.get("/portafoglio/{pos_id}", response_class=HTMLResponse)
def dettaglio(request: Request, pos_id: int):
    """Scheda di dettaglio di una posizione (ETF: fondo+holdings; azione: profilo)."""
    with SessionLocal() as db:
        p = db.get(Position, pos_id)
    if not p:
        return RedirectResponse("/portafoglio", status_code=303)
    q = market.quotes_map().get((p.ticker or "").upper())
    fund = market.get_fundamentals(p.ticker, tipo=p.tipo) if (p.ticker or "").strip() else None
    perf = None
    if (p.ticker or "").strip():
        closes = market.history_closes(market._yahoo_symbol(p.ticker), "1y", "1wk")
        if len(closes) >= 2 and closes[0]:
            perf = round((closes[-1] / closes[0] - 1) * 100, 2)
    return templates.TemplateResponse(request, "portfolio_detail.html", {
        "active": "portafoglio", "p": p, "q": q, "fund": fund, "perf": perf,
    })
