"""Logica del portafoglio: calcolatore PAC e riepiloghi.

Tutto OFFLINE in Fase 1. Niente segnali operativi, niente 'compra/vendi':
l'app calcola e mostra, la decisione resta sempre dell'utente.
"""
from sqlalchemy import select

from shared.db import SessionLocal
from portfolio.models import Position


def lista_posizioni() -> list[Position]:
    with SessionLocal() as db:
        return list(db.execute(
            select(Position).order_by(Position.ordine, Position.id)
        ).scalars().all())


def somma_target() -> float:
    """Somma delle % target (deve fare 100; gli asset a importo fisso non contano)."""
    return round(sum(p.pct_target for p in lista_posizioni() if not p.is_fisso), 4)


def calcola_pac(importo_mensile: float) -> dict:
    """Ripartisce l'importo mensile fra gli asset secondo la % target.

    - quota per asset = importo_mensile x % target (arrotondata al centesimo)
    - asset a importo fisso (Take-Two): quota fissa, con % implicita a parte
    - controllo arrotondamenti: scostamento fra somma quote e importo
    - controllo allocazione: la somma delle % deve fare 100
    """
    posizioni = lista_posizioni()
    importo = max(0.0, float(importo_mensile or 0))

    righe, righe_fisse = [], []
    somma_pct = 0.0
    somma_quote = 0.0
    somma_fissi = 0.0

    for p in posizioni:
        if p.is_fisso:
            implicita = (p.importo_fisso / importo * 100) if importo > 0 else 0.0
            somma_fissi += p.importo_fisso
            righe_fisse.append({
                "nome": p.nome, "ticker": p.ticker, "categoria": p.categoria,
                "importo": round(p.importo_fisso, 2), "pct_implicita": implicita,
            })
        else:
            quota = round(importo * p.pct_target / 100.0, 2)
            somma_pct += p.pct_target
            somma_quote += quota
            righe.append({
                "nome": p.nome, "ticker": p.ticker, "tipo": p.tipo,
                "categoria": p.categoria, "pct_target": p.pct_target, "quota": quota,
            })

    somma_quote = round(somma_quote, 2)
    scostamento = round(somma_quote - importo, 2)   # per arrotondamenti ai centesimi
    return {
        "importo_mensile": round(importo, 2),
        "righe": righe,
        "righe_fisse": righe_fisse,
        "somma_pct": round(somma_pct, 4),
        "somma_quote": somma_quote,
        "somma_fissi": round(somma_fissi, 2),
        "scostamento": scostamento,
        "totale_mensile": round(somma_quote + somma_fissi, 2),
        "pct_ok": abs(somma_pct - 100.0) < 0.01,
        "n_asset": len(righe),
    }


def riepilogo() -> dict:
    """Numeri di sintesi per la dashboard (Fase 1: solo cio' che e' offline)."""
    posizioni = lista_posizioni()
    a_pct = [p for p in posizioni if not p.is_fisso]
    valore = sum(p.valore_posseduto or 0 for p in posizioni)
    return {
        "n_posizioni": len(posizioni),
        "n_etf": sum(1 for p in posizioni if p.tipo == "ETF"),
        "n_azioni": sum(1 for p in posizioni if p.tipo == "Azione"),
        "somma_target": round(sum(p.pct_target for p in a_pct), 4),
        "target_ok": abs(sum(p.pct_target for p in a_pct) - 100.0) < 0.01,
        "valore_posseduto": round(valore, 2),
        "ha_valori": valore > 0,
    }
