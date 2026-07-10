"""Pagine del portafoglio: elenco posizioni, aggiungi/modifica/elimina, PAC.

Tutto modificabile dall'interfaccia, MAI da codice (come da requisiti).
"""
import json
import urllib.parse
from datetime import datetime

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse

from shared.db import SessionLocal
from shared.templating import templates
from shared.parsing import to_float, to_date
from shared.charts import chart_points
from shared import ai, settings_store
from portfolio.models import Position, TIPO_ETF, TIPO_AZIONE
from portfolio import service, market, analytics

router = APIRouter()


@router.get("/analisi", response_class=HTMLResponse)
def analisi(request: Request):
    return templates.TemplateResponse(request, "analisi.html", {
        "active": "analisi",
        "lt": analytics.look_through(),
        "an": analytics.analisi_completa(),
        "risk": analytics.get_cached_risk(),
        "ai_on": ai.is_configured(),
    })


@router.post("/analisi/ai")
async def analisi_ai(label: str = Form(""), valore: str = Form("")):
    """Spiega una metrica dell'analisi (popup ✨): risposta JSON per il modal."""
    from fastapi.responses import JSONResponse
    label, valore = (label or "").strip()[:120], (valore or "").strip()[:60]
    if not label:
        return JSONResponse({"ok": False, "error": "vuoto"})
    lt = analytics.look_through()
    settori = ", ".join(f"{s['key']} {s['pct']}%" for s in lt["settori"][:6])
    contesto = (f"Portafoglio personale diversificato: {lt['n_titoli']} titoli; "
                f"settori principali: {settori or 'n/d'}.")
    return JSONResponse(ai.spiega_metrica(label, valore, contesto))


@router.post("/analisi/rischio")
def calcola_rischio():
    analytics.compute_risk()
    return RedirectResponse("/analisi", status_code=303)


@router.get("/portafoglio", response_class=HTMLResponse)
def elenco(request: Request):
    vista = service.vista_portafoglio()
    snapshot = market.get_perf_snapshot()
    # perf ~12 mesi del portafoglio: media pesata sui titoli con storia nota
    num = den = 0.0
    for r in vista["righe"]:
        p = r["p"]
        pf = snapshot.get((p.ticker or "").upper())
        if pf is None:
            continue
        w = r["valore"] or (p.pct_target if not p.is_fisso else 0)
        if w:
            num += w * pf
            den += w
    qp = request.query_params
    return templates.TemplateResponse(request, "portfolio_positions.html", {
        "active": "portafoglio",
        "vista": vista,
        "riepilogo": service.riepilogo(vista),
        "perf": snapshot,                            # P/L ~12m per ticker
        "pf_perf": round(num / den, 2) if den else None,
        "flash_added": qp.get("added", ""),
        "flash_deleted": qp.get("deleted", ""),
        "flash_saved": qp.get("saved", "") == "1",
        "open_form": qp.get("add", "") == "1",       # apre il form inline
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
    nome_breve: str = Form(""),
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
        nome_breve=nome_breve.strip(),
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
        if pos_id.strip().isdigit():            # modifica di una posizione esistente
            p = db.get(Position, int(pos_id))
            if p:
                for k, v in dati.items():
                    setattr(p, k, v)
            db.commit()
            return RedirectResponse("/portafoglio?saved=1", status_code=303)
        # nuova posizione, in fondo all'elenco
        ultimo = db.query(Position).order_by(Position.ordine.desc()).first()
        dati["ordine"] = (ultimo.ordine + 1) if ultimo else 0
        db.add(Position(**dati))
        db.commit()
    etichetta = urllib.parse.quote(dati["ticker"] or dati["nome"])
    return RedirectResponse(f"/portafoglio?added={etichetta}", status_code=303)


@router.post("/portafoglio/{pos_id}/elimina")
def elimina(pos_id: int):
    etichetta = ""
    with SessionLocal() as db:
        p = db.get(Position, pos_id)
        if p:
            etichetta = p.ticker or p.nome
            db.delete(p)
            db.commit()
    return RedirectResponse(
        f"/portafoglio?deleted={urllib.parse.quote(etichetta)}", status_code=303)


@router.get("/pac", response_class=HTMLResponse)
def pac(request: Request, importo: str = ""):
    importo = (importo or "").strip() or "500"
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


def _ai_take_cached(ticker: str) -> dict | None:
    """L'analisi AI della posizione, se già generata (cache per ticker)."""
    raw = settings_store.get_setting(f"ai_take_{(ticker or '').upper()}", "")
    if not raw:
        return None
    try:
        saved = json.loads(raw)
        return {"text": saved.get("text", ""), "conf": saved.get("conf", "media")}
    except json.JSONDecodeError:
        return None


def _descrizione_pubblica(p, fund, perf) -> str:
    """Descrizione SOLO da dati pubblici (mai ISIN/quantità/valori posseduti)."""
    righe = [f"Strumento: {p.nome} ({p.ticker}), tipo {p.tipo}, categoria {p.categoria or 'n/d'}."]
    if fund:
        if p.tipo == "ETF":
            settori = ", ".join(f"{s['name']} {s['weight']}%" for s in (fund.get("sectors") or [])[:5])
            righe.append(f"Categoria fondo: {fund.get('category') or 'n/d'}; settori principali: {settori or 'n/d'}.")
            top = ", ".join(h.get("name") or h.get("symbol") or "" for h in (fund.get("holdings") or [])[:5])
            if top:
                righe.append(f"Prime posizioni (parziale): {top}.")
        else:
            righe.append(f"Settore: {fund.get('sector') or 'n/d'}; industria: {fund.get('industry') or 'n/d'}; "
                         f"paese: {fund.get('country') or 'n/d'}; beta: {fund.get('beta') or 'n/d'}.")
        if fund.get("div_yield"):
            righe.append(f"Rendimento da dividendo: {round(fund['div_yield'] * 100, 2)}%.")
    if perf is not None:
        righe.append(f"Performance ~12 mesi: {perf}%.")
    return "\n".join(righe)


# domicilio dello strumento dal prefisso ISIN (dato reale, nessuna stima)
_ISIN_PAESE = {
    "IE": "Irlanda", "LU": "Lussemburgo", "US": "Stati Uniti", "IT": "Italia",
    "DE": "Germania", "FR": "Francia", "GB": "Regno Unito", "NL": "Paesi Bassi",
    "CH": "Svizzera", "ES": "Spagna", "JE": "Jersey", "GG": "Guernsey",
}


@router.get("/portafoglio/{pos_id}", response_class=HTMLResponse)
def dettaglio(request: Request, pos_id: int):
    """Scheda di dettaglio di una posizione (ETF: fondo+holdings; azione: profilo),
    con grafico ~12 mesi e, se generata, l'analisi qualitativa dell'agente."""
    with SessionLocal() as db:
        p = db.get(Position, pos_id)
    if not p:
        return RedirectResponse("/portafoglio", status_code=303)
    q = market.quotes_map().get((p.ticker or "").upper())
    fund = market.get_fundamentals(p.ticker, tipo=p.tipo) if (p.ticker or "").strip() else None
    perf = None
    punti, sale = "", True
    if (p.ticker or "").strip():
        closes = market.history_closes(market._yahoo_symbol(p.ticker), "1y", "1wk")
        if len(closes) >= 2 and closes[0]:
            perf = round((closes[-1] / closes[0] - 1) * 100, 2)
            punti, sale = chart_points(closes)
    if fund is not None:
        fund["ai"] = _ai_take_cached(p.ticker)
    # ?panel=1 -> solo il frammento per il DRAWER (aperto da app.js sopra
    # l'elenco, come nel design); senza parametro -> pagina intera.
    tpl = "portfolio_detail_panel.html" if request.query_params.get("panel") \
        else "portfolio_detail.html"
    return templates.TemplateResponse(request, tpl, {
        "active": "portafoglio", "p": p, "q": q, "fund": fund, "perf": perf,
        "chart_points": punti, "chart_up": sale, "ai_on": ai.is_configured(),
        "domicilio": _ISIN_PAESE.get((p.isin or "")[:2].upper()),
    })


@router.post("/portafoglio/{pos_id}/ai")
def genera_ai_take(pos_id: int):
    """Genera (o rigenera) l'analisi dell'agente per una posizione e la salva."""
    with SessionLocal() as db:
        p = db.get(Position, pos_id)
    if not p or not (p.ticker or "").strip():
        return RedirectResponse("/portafoglio", status_code=303)
    fund = market.get_fundamentals(p.ticker, tipo=p.tipo)
    perf = None
    closes = market.history_closes(market._yahoo_symbol(p.ticker), "1y", "1wk")
    if len(closes) >= 2 and closes[0]:
        perf = round((closes[-1] / closes[0] - 1) * 100, 2)
    res = ai.analizza_posizione(_descrizione_pubblica(p, fund, perf))
    if res.get("ok"):
        settings_store.set_setting(f"ai_take_{p.ticker.upper()}", json.dumps({
            "text": res["text"], "conf": res["conf"],
            "when": datetime.now().isoformat(timespec="minutes")}))
    return RedirectResponse(f"/portafoglio/{pos_id}", status_code=303)
