"""Agente AI condiviso — fondamenta (Fase 4, parte 1).

Qui c'è solo lo STRATO DI BASE: connessione a Gemini, prova connessione, modello
configurabile e l'interruttore doppia modalità. Le funzioni che mandano dati
(inserimento spese in linguaggio naturale, analisi) e il filtro privacy per sezione
arriveranno nei passi successivi.

Filosofia dell'agente (dal CLAUDE.md del news-monitor):
- mai segnali operativi (compra/vendi/entra/esci);
- non è un oracolo: non prevede i prezzi; ogni stima ha un livello di confidenza
  dichiarato (bassa/media/alta) e un disclaimer;
- italiano semplice, onestà intellettuale, ridurre il rumore;
- la decisione finale resta sempre dell'utente.

Provider ASTRATTO: oggi Gemini (free tier di Google AI Studio); domani Vertex AI o
Claude si innestano qui senza toccare il resto. La chiave sta solo in locale
(database), mai nei log né nell'URL (passata via header).
"""
import json
import urllib.error
import urllib.request

from shared import settings_store as store

DEFAULT_MODEL = "gemini-2.0-flash"        # modello gratuito; modificabile in Impostazioni
DEFAULT_FALLBACK = "gemini-2.0-flash-lite"  # ripiego se i limiti del principale sono esauriti
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

MODE_ON_DEMAND = "a_domanda"
MODE_PROACTIVE = "proattivo"
MODES = (MODE_ON_DEMAND, MODE_PROACTIVE)

SYSTEM_PROMPT = (
    "Sei l'assistente personale di un'app di finanza a uso privato. Regole non negoziabili: "
    "1) MAI segnali operativi (compra/vendi/entra/esci) né consigli personalizzati su cosa fare coi soldi. "
    "2) Non sei un oracolo: non prevedi i prezzi; ogni stima è un'analisi qualitativa con un livello di "
    "confidenza dichiarato (bassa/media/alta) e un breve disclaimer. "
    "3) Italiano semplice, frasi brevi, onestà intellettuale: se non sai, dillo; non inventare numeri. "
    "4) Sei descrittivo, non prescrittivo: mostri fatti e pattern, la decisione resta all'utente."
)


def get_model() -> str:
    return store.get_setting("gemini_model", "").strip() or DEFAULT_MODEL


def set_model(value: str) -> None:
    store.set_setting("gemini_model", (value or "").strip())


def get_mode() -> str:
    m = store.get_setting("ai_mode", MODE_ON_DEMAND)
    return m if m in MODES else MODE_ON_DEMAND


def set_mode(value: str) -> None:
    if value in MODES:
        store.set_setting("ai_mode", value)


def is_configured() -> bool:
    """True se è stata inserita la chiave Gemini (l'agente è sbloccato)."""
    return store.has_key("gemini_api_key")


def _call(prompt: str, system: str = SYSTEM_PROMPT, timeout: int = 20) -> str:
    key = store.get_setting("gemini_api_key", "").strip()
    if not key:
        raise RuntimeError("no_key")
    url = ENDPOINT.format(model=get_model())
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system}]},
        "generationConfig": {"temperature": 0.4},
    }
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": key})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read())
    cands = data.get("candidates") or []
    if not cands:
        raise ValueError("risposta vuota")
    parts = cands[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts).strip()


def test_connection() -> tuple[bool, str]:
    """Prova la connessione con un mini-prompt. Ritorna (ok, dettaglio)."""
    if not is_configured():
        return (False, "no_key")
    try:
        txt = _call("Rispondi solo con la parola: OK", timeout=15)
        return (True, (txt or "").strip()[:120] or "OK")
    except urllib.error.HTTPError as e:
        detail = "401/403" if e.code in (401, 403) else str(e.code)
        return (False, f"HTTP {detail}")
    except urllib.error.URLError:
        return (False, "rete")
    except Exception as e:
        return (False, type(e).__name__)
