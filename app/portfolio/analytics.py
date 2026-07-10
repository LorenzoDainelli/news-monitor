"""Analisi del portafoglio: look-through settoriale e metriche di rischio.

Tutto DESCRITTIVO, mai prescrittivo: mostra fatti (esposizioni, volatilità, ...)
così decidi tu. Niente segnali operativi. I dati mancanti restano fuori dal calcolo
e la copertura viene dichiarata (onestà intellettuale).
"""
import json
import math
from datetime import datetime

from portfolio import market
from portfolio.service import lista_posizioni, vista_portafoglio
from shared import settings_store


def _sector_key(label: str) -> str:
    s = (label or "").strip().lower().replace(" ", "_")
    return "realestate" if s == "real_estate" else s


def look_through(cached_only: bool = False) -> dict:
    """Esposizione settoriale aggregata (ETF per pesi settoriali, azioni per settore),
    pesata sulla % target. Più rendimento da dividendo e diversificazione.
    Con cached_only=True legge SOLO la cache locale (mai HTTP): per la dashboard."""
    posizioni = [p for p in lista_posizioni() if not p.is_fisso and (p.ticker or "").strip()]
    fetch = market.get_fundamentals_cached if cached_only else market.get_fundamentals
    sett: dict[str, float] = {}
    coperto = 0.0
    div_acc = div_w = 0.0
    for p in posizioni:
        f = fetch(p.ticker) if cached_only else fetch(p.ticker, tipo=p.tipo)
        if not f:
            continue
        w = p.pct_target
        coperto += w
        if p.tipo == "ETF" and f.get("sectors"):
            for s in f["sectors"]:
                sett[s["name"]] = sett.get(s["name"], 0.0) + w * s["weight"] / 100.0
        elif f.get("sector"):
            k = _sector_key(f["sector"])
            sett[k] = sett.get(k, 0.0) + w
        if f.get("div_yield"):
            div_acc += w * f["div_yield"]
            div_w += w
    settori = []
    if coperto > 0:
        for k, v in sorted(sett.items(), key=lambda x: -x[1]):
            settori.append({"key": k, "pct": round(v / coperto * 100, 1)})
    tech = next((s["pct"] for s in settori if s["key"] == "technology"), 0.0)
    weights = [p.pct_target for p in posizioni]
    sw = sum(weights)
    hhi = sum((x / sw) ** 2 for x in weights) if sw else 0
    return {
        "settori": settori,
        "tech": tech,
        "tech_alert": tech > 50,
        "coperto": round(coperto, 1),
        "totale_target": round(sw, 1),
        "div_yield": round(div_acc / div_w * 100, 2) if div_w else None,
        "eff_holdings": round(1 / hhi, 1) if hhi else 0,
        "n_titoli": len(posizioni),
    }


def analisi_completa() -> dict:
    """Sintesi, diversificazione, stile e look-through per titolo (design MyMoney).

    Pesi: il VALORE reale se inserito (quantità/valori), altrimenti la % target.
    Il reddito da dividendi in euro esiste solo coi valori reali. I dati mancanti
    restano None: la pagina li mostra vuoti, mai inventati."""
    vista = vista_portafoglio()
    snapshot = market.get_perf_snapshot()
    usa_valori = vista["ha_totale"]

    pesi = []           # (posizione, peso, fondamentali, quotazione)
    for r in vista["righe"]:
        p = r["p"]
        if p.is_fisso:
            continue
        w = r["valore"] if usa_valori else p.pct_target
        if not w:
            continue
        f = market.get_fundamentals(p.ticker, tipo=p.tipo) if (p.ticker or "").strip() else None
        pesi.append((p, float(w), f, r.get("q")))
    somma = sum(w for _, w, _, _ in pesi) or 1.0

    perf_n = perf_d = 0.0
    div_n = div_d = reddito = 0.0
    ter_n = ter_d = 0.0
    etf_w = 0.0
    expo: dict[str, float] = {}
    valute: dict[str, float] = {}       # valuta di QUOTAZIONE (dato reale)
    geo: dict[str, float] = {}          # paese: noto solo per le azioni
    geo_cop = 0.0
    for p, w, f, q in pesi:
        pf = snapshot.get((p.ticker or "").upper())
        if pf is not None:
            perf_n += w * pf
            perf_d += w
        if p.tipo == "ETF":
            etf_w += w
        if f:
            if f.get("div_yield"):
                div_n += w * f["div_yield"]
                div_d += w
                if usa_valori:
                    reddito += w * f["div_yield"]
            if p.tipo == "ETF" and f.get("expense_ratio"):
                ter_n += w * f["expense_ratio"]
                ter_d += w
            # esposizione reale: quote dentro gli ETF + azioni dirette
            if p.tipo == "ETF" and f.get("holdings"):
                for h in f["holdings"]:
                    nome = h.get("name") or h.get("symbol") or ""
                    peso_h = (h.get("weight") or 0) / 100.0
                    if nome and peso_h:
                        expo[nome] = expo.get(nome, 0.0) + w / somma * peso_h
        if p.tipo != "ETF":
            expo[p.nome] = expo.get(p.nome, 0.0) + w / somma
            if f and f.get("country"):
                geo[f["country"]] = geo.get(f["country"], 0.0) + w
                geo_cop += w
        cur = (q.currency if (q and q.ok and q.currency) else None)
        if cur:
            valute[cur] = valute.get(cur, 0.0) + w

    ordinati = sorted(pesi, key=lambda x: -x[1])
    top1 = round(ordinati[0][1] / somma * 100, 1) if ordinati else None
    top1_tk = ordinati[0][0].ticker if ordinati else ""
    top5 = round(sum(w for _, w, _, _ in ordinati[:5]) / somma * 100, 1) if ordinati else None
    look = [{"n": n, "w": round(v * 100, 1)} for n, v in
            sorted(expo.items(), key=lambda x: -x[1])[:8]]
    lista_valute = [{"n": k, "w": round(v / somma * 100, 1)} for k, v in
                    sorted(valute.items(), key=lambda x: -x[1])]
    lista_geo = [{"n": k, "w": round(v / geo_cop * 100, 1)} for k, v in
                 sorted(geo.items(), key=lambda x: -x[1])] if geo_cop else []

    return {
        "valute": lista_valute,
        "geo": lista_geo,
        "geo_coverage": round(geo_cop / somma * 100, 1) if geo_cop else 0,
        "usa_valori": usa_valori,
        "valore_totale": vista["totale"] if usa_valori else None,
        "perf12m": round(perf_n / perf_d, 2) if perf_d else None,
        "div_yield": round(div_n / div_d * 100, 2) if div_d else None,
        "div_income": round(reddito, 2) if (usa_valori and reddito) else None,
        "ter": round(ter_n / ter_d * 100, 2) if ter_d else None,
        "quota_etf": round(etf_w / somma * 100, 1) if pesi else None,
        "top1": top1, "top1_tk": top1_tk, "top5": top5,
        "look": look, "look_max": look[0]["w"] if look else 1,
        "n_titoli": len(pesi),
    }


def _weekly_returns(closes: list) -> list:
    return [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes)) if closes[i - 1]]


def compute_risk() -> dict | None:
    """Metriche di rischio del portafoglio (pesate sulla % target), su ~1 anno
    di dati settimanali. Calcolo pesante: lo lanciamo a richiesta e lo salviamo."""
    posizioni = [p for p in lista_posizioni() if not p.is_fisso and (p.ticker or "").strip()]
    rets, tot_w = [], 0.0
    for p in posizioni:
        r = _weekly_returns(market.history_closes(market._yahoo_symbol(p.ticker), "1y", "1wk"))
        if len(r) >= 30:
            rets.append((p.pct_target, r))
            tot_w += p.pct_target
    bench = _weekly_returns(market.history_closes(market._yahoo_symbol("IWDA"), "1y", "1wk"))
    if not rets or not bench or tot_w <= 0:
        return None
    L = min(min(len(r) for _, r in rets), len(bench))
    port = [0.0] * L
    for w, r in rets:
        rr = r[-L:]
        for i in range(L):
            port[i] += (w / tot_w) * rr[i]
    b = bench[-L:]
    mean = sum(port) / L
    var = sum((x - mean) ** 2 for x in port) / (L - 1)
    vol = math.sqrt(var) * math.sqrt(52)
    cum = peak = 1.0
    mdd = 0.0
    for x in port:
        cum *= (1 + x)
        peak = max(peak, cum)
        mdd = min(mdd, cum / peak - 1)
    ann = (1 + mean) ** 52 - 1
    bmean = sum(b) / L
    cov = sum((port[i] - mean) * (b[i] - bmean) for i in range(L)) / (L - 1)
    bvar = sum((x - bmean) ** 2 for x in b) / (L - 1)
    snap = {
        "vol": round(vol * 100, 1),
        "mdd": round(mdd * 100, 1),
        "sharpe": round((ann - 0.02) / vol, 2) if vol else None,
        "beta": round(cov / bvar, 2) if bvar else None,
        # perdita mensile attesa max al 95% (parametrica) e correlazione col mercato
        "var95m": round(vol / math.sqrt(12) * 1.645 * 100, 1),
        "r2": round(cov * cov / (var * bvar) * 100, 1) if (var and bvar) else None,
        "ann": round(ann * 100, 1),
        "n": len(rets),
        "weeks": L,
        "when": market.fmt_ts(datetime.utcnow()),
    }
    settings_store.set_setting("risk_snapshot", json.dumps(snap))
    return snap


def get_cached_risk() -> dict | None:
    raw = settings_store.get_setting("risk_snapshot", "")
    return json.loads(raw) if raw else None
