"""Analisi del portafoglio: look-through settoriale e metriche di rischio.

Tutto DESCRITTIVO, mai prescrittivo: mostra fatti (esposizioni, volatilità, ...)
così decidi tu. Niente segnali operativi. I dati mancanti restano fuori dal calcolo
e la copertura viene dichiarata (onestà intellettuale).
"""
import json
import math
from datetime import datetime

from portfolio import market
from portfolio.service import lista_posizioni
from shared import settings_store


def _sector_key(label: str) -> str:
    s = (label or "").strip().lower().replace(" ", "_")
    return "realestate" if s == "real_estate" else s


def look_through() -> dict:
    """Esposizione settoriale aggregata (ETF per pesi settoriali, azioni per settore),
    pesata sulla % target. Più rendimento da dividendo e diversificazione."""
    posizioni = [p for p in lista_posizioni() if not p.is_fisso and (p.ticker or "").strip()]
    sett: dict[str, float] = {}
    coperto = 0.0
    div_acc = div_w = 0.0
    for p in posizioni:
        f = market.get_fundamentals(p.ticker, tipo=p.tipo)
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
