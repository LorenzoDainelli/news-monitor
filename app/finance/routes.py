"""Pagine delle finanze: la panoramica è l'unica pagina (card portafogli,
movimento nuovo, sintesi del mese, TUTTI i movimenti)."""
import json
from datetime import datetime

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from shared.templating import templates
from shared.parsing import to_float, to_datetime
from shared import ai, settings_store
from finance import service
from finance.models import TIPO_ENTRATA, TIPO_USCITA, TIPO_TRASFERIMENTO, TIPO_GIRO

router = APIRouter()


def _oggi_local():
    # ora LOCALE del PC (l'app è locale): utcnow() precompilava il form 1-2 ore indietro
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


def _lettura_ai_salvata():
    """L'ultima 'lettura AI' delle finanze, se generata (persistente)."""
    raw = settings_store.get_setting("fin_ai", "")
    if not raw:
        return None
    try:
        saved = json.loads(raw)
        return {"text": saved.get("text", ""), "conf": saved.get("conf", "media")}
    except json.JSONDecodeError:
        return None


def _ctx_panoramica() -> dict:
    now = datetime.now()
    return {
        "active": "finanze",
        "saldi": service.saldi(),
        "riep": service.riepilogo_mese(now.year, now.month),
        "movimenti": service.lista_movimenti(),      # TUTTI, data desc
        "wallets": service.wallets(),
        "categorie": service.categorie(),
        "tipi": (TIPO_ENTRATA, TIPO_USCITA, TIPO_TRASFERIMENTO, TIPO_GIRO),
        "giri_aperti": service.giri_aperti(),        # riquadro "In attesa di rimborso"
        "controparti": service.controparti(),        # suggerimenti "da chi"
        "oggi": _oggi_local(),
        "ai_on": ai.is_configured(),
        "lettura_ai": _lettura_ai_salvata(),
    }


# ------------------------------ panoramica ------------------------------
@router.get("/finanze", response_class=HTMLResponse)
def panoramica(request: Request):
    return templates.TemplateResponse(request, "finance_overview.html", _ctx_panoramica())


@router.post("/finanze/movimenti/salva")
def salva_movimento(
    tipo: str = Form(...),
    data: str = Form(""),
    importo: str = Form("0"),
    wallet_id: int = Form(...),
    wallet_to_id: str = Form(""),
    categoria: str = Form(""),
    descrizione: str = Form(""),
    # --- solo partite di giro ---
    controparte: str = Form(""),
    giro_dopo: str = Form(""),             # checkbox: il rimborso arriverà dopo
    importo_ricevuto: str = Form(""),
    data_ricevuto: str = Form(""),
    wallet_ricevuto_id: str = Form(""),
    next: str = Form("/finanze"),
):
    wto = int(wallet_to_id) if (wallet_to_id or "").strip().isdigit() else None
    if tipo in (TIPO_ENTRATA, TIPO_USCITA, TIPO_TRASFERIMENTO):
        service.crea_movimento(
            tipo=tipo, data=to_datetime(data), importo=to_float(importo, 0.0) or 0.0,
            wallet_id=wallet_id, wallet_to_id=wto, categoria_nome=categoria,
            descrizione=descrizione)
    elif tipo == TIPO_GIRO:
        # con la casella "rimborso dopo" la gamba ricevuta si ignora: partita APERTA
        ricevuto = None if giro_dopo else to_float(importo_ricevuto, None)
        wric = int(wallet_ricevuto_id) if (wallet_ricevuto_id or "").strip().isdigit() else None
        service.crea_giro(
            data=to_datetime(data), importo=to_float(importo, 0.0) or 0.0,
            wallet_id=wallet_id, controparte=controparte, descrizione=descrizione,
            importo_ricevuto=ricevuto,
            data_ricevuto=to_datetime(data_ricevuto) if ricevuto is not None else None,
            wallet_to_id=wric if ricevuto is not None else None)
    dest = next if next.startswith("/finanze") else "/finanze"
    return RedirectResponse(dest, status_code=303)


@router.post("/finanze/movimenti/{tid}/elimina")
def elimina_movimento(tid: int, next: str = Form("/finanze")):
    service.elimina_movimento(tid)
    dest = next if next.startswith("/finanze") else "/finanze"
    return RedirectResponse(dest, status_code=303)


# ------------------------------ partite di giro ------------------------------
@router.post("/finanze/giro/{tid}/chiudi")
def giro_chiudi(
    tid: int,
    importo_ricevuto: str = Form("0"),
    data_ricevuto: str = Form(""),
    wallet_ricevuto_id: int = Form(...),
    next: str = Form("/finanze"),
):
    """Registra il rimborso di una partita aperta: da qui la differenza entra
    nelle statistiche (guadagno alla data del rimborso, perdita a quella della
    spesa)."""
    imp = to_float(importo_ricevuto, None)
    if imp is not None:
        service.chiudi_giro(tid, importo_ricevuto=imp,
                            data_ricevuto=to_datetime(data_ricevuto),
                            wallet_to_id=wallet_ricevuto_id)
    dest = next if next.startswith("/finanze") else "/finanze"
    return RedirectResponse(dest, status_code=303)


@router.post("/finanze/giro/{tid}/converti")
def giro_converti(tid: int, next: str = Form("/finanze")):
    """'Non me li ridaranno': la partita aperta diventa una normale uscita."""
    service.converti_giro_in_uscita(tid)
    dest = next if next.startswith("/finanze") else "/finanze"
    return RedirectResponse(dest, status_code=303)


# ------------------------------ agente AI (Fase 4) ------------------------------
@router.post("/finanze/ai/parse", response_class=HTMLResponse)
def ai_parse(request: Request, testo: str = Form(""), next: str = Form("/finanze")):
    """Interpreta una frase ('ieri 20€ di benzina con la carta') e mostra il modulo
    movimenti PRECOMPILATO. Non salva nulla: la conferma resta all'utente."""
    ctx = _ctx_panoramica()
    ctx["proposta"] = ai.parse_movimento(testo, ctx["wallets"], ctx["categorie"])
    # il modulo precompilato deve tornare a una pagina GET reale dopo il salvataggio
    # (cur_path qui sarebbe /finanze/ai/parse, che non ha una GET)
    ctx["next_url"] = "/finanze"
    return templates.TemplateResponse(request, "finance_overview.html", ctx)


def _mesi_indietro(now, k):
    y, m = now.year, now.month - k
    while m <= 0:
        m += 12
        y -= 1
    return y, m


def _contesto_finanze() -> str:
    """Riassunto AGGREGATO e anonimo degli ultimi 3 mesi per l'analisi AI.
    Niente nomi/carte/IBAN: solo totali e categorie."""
    now = datetime.now()
    righe = []
    for k in (2, 1, 0):
        y, m = _mesi_indietro(now, k)
        r = service.riepilogo_mese(y, m)
        cat = "; ".join(f"{c['nome']}: {c['tot']:.0f}€" for c in r["spese_categoria"][:6]) or "nessuna"
        righe.append(
            f"Mese {y}-{m:02d}: entrate {r['entrate']:.0f}€, uscite {r['uscite']:.0f}€, "
            f"saldo {r['saldo']:.0f}€. Spese principali per categoria: {cat}.")
    sal = service.saldi()
    righe.append(f"Patrimonio totale attuale: {sal['totale']:.0f}€ distribuito su "
                 f"{len(sal['righe'])} portafogli.")
    return "\n".join(righe)


@router.post("/finanze/ai/analisi")
def ai_analisi():
    """Analisi descrittiva del mese (dati aggregati e anonimi): la genera,
    la SALVA (resta visibile come 'Lettura AI') e torna in panoramica."""
    res = ai.analizza_finanze(_contesto_finanze())
    if res.get("ok"):
        settings_store.set_setting("fin_ai", json.dumps({
            "text": res["text"], "conf": res.get("conf", "media"),
            "when": datetime.now().isoformat(timespec="minutes")}))
    return RedirectResponse("/finanze", status_code=303)
