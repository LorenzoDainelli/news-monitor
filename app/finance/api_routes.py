"""API JSON delle Finanze (v2, vedi PIANO-V2.md).

Espone in JSON ciò che le pagine mostrano in HTML, così la PWA sul telefono può
leggere lo stato e sincronizzare i movimenti. Gira sullo stesso server locale
(127.0.0.1): nessuna nuova esposizione, nessuna autenticazione nuova finché
l'app non esce dal PC.

I riferimenti tra record usano lo `uid` (stabile tra dispositivi), mai l'id interno.

Fase 4: canale di scrittura bidirezionale (POST /ops, GET /diary, GET /snapshot,
GET /export, POST /import).
"""
import json

from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import JSONResponse, Response

from finance import service
from shared import sync

router = APIRouter(prefix="/api/finanze", tags=["finanze-api"])


# ── Fase 1: sola lettura ────────────────────────────────────────────────────

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


# ── Fase 4: sync bidirezionale ──────────────────────────────────────────────

@router.post("/ops")
async def api_ops(request: Request):
    """La PWA manda le sue operazioni: il PC le applica con merge LWW.

    Body JSON: {schema, device_id, ops: [...]}
    Ritorna: {ok, applied, skipped, errors, server_device_id, diary_lines}
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "json_invalido"}, status_code=400)
    ops = body.get("ops", [])
    if not isinstance(ops, list):
        return JSONResponse({"ok": False, "error": "ops_non_lista"}, status_code=400)
    source_device = body.get("device_id", "")
    result = sync.import_ops(ops, source_device_id=source_device)
    return {
        "ok": True,
        **result,
        "server_device_id": sync.get_device_id(),
        "diary_lines": sync.diary_lines_count(),
    }


@router.get("/diary")
def api_diary(since: int = 0):
    """Il client scarica il diario del PC dal cursore `since` in poi (0 = tutte).

    Ritorna: {ok, device_id, since, ops: [...], total_lines}
    """
    ops = sync.export_diary(since_line=since)
    return {
        "ok": True,
        "device_id": sync.get_device_id(),
        "since": since,
        "ops": ops,
        "total_lines": sync.diary_lines_count(),
    }


@router.get("/snapshot")
def api_snapshot():
    """Fotografia completa: per il primo avvio di un dispositivo nuovo."""
    return sync.build_snapshot()


@router.get("/export")
def api_export():
    """Scarica un bundle JSON (snapshot + diario) come file. Fallback manuale."""
    bundle = sync.export_bundle()
    content = json.dumps(bundle, ensure_ascii=False, default=str, indent=2)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="mymoney-export.json"'},
    )


@router.post("/import")
async def api_import(request: Request):
    """Carica un bundle JSON di export da un altro dispositivo.

    Accetta sia un JSON nel body sia un file multipart.
    Ritorna: {ok, applied, skipped, errors}
    """
    content_type = request.headers.get("content-type", "")
    try:
        if "multipart" in content_type:
            form = await request.form()
            file = form.get("file")
            if file and hasattr(file, "read"):
                raw = await file.read()
                data = json.loads(raw)
            else:
                return JSONResponse({"ok": False, "error": "file_mancante"}, status_code=400)
        else:
            data = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "json_invalido"}, status_code=400)
    result = sync.import_bundle(data)
    return {"ok": True, **result}
