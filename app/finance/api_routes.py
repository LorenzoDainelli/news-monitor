"""API JSON delle Finanze (v2, vedi PIANO-V2.md).

Espone in JSON ciò che le pagine mostrano in HTML, così la PWA sul telefono può
leggere lo stato e (in futuro, Fase 4) sincronizzare i movimenti. SOLA LETTURA in
Fase 1. Gira sullo stesso server locale (127.0.0.1): nessuna nuova esposizione,
nessuna autenticazione nuova finché l'app non esce dal PC.

I riferimenti tra record usano lo `uid` (stabile tra dispositivi), mai l'id interno.
"""
from fastapi import APIRouter

from finance import service

router = APIRouter(prefix="/api/finanze", tags=["finanze-api"])


@router.get("/stato")
def api_stato():
    """Portafogli (con saldo attuale), categorie e sintesi del mese corrente."""
    return service.stato_sync()


@router.get("/movimenti")
def api_movimenti(since: str = "", limit: int = 0):
    """Movimenti in formato sync. `since` (ISO-8601) = solo quelli modificati dopo
    quel momento; `limit` = massimo numero di righe."""
    movimenti = service.movimenti_sync(since=since or None, limit=limit or None)
    return {"count": len(movimenti), "movimenti": movimenti}
