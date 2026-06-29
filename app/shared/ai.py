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
import re
import urllib.error
import urllib.request
from datetime import datetime

from shared import settings_store as store
from shared import privacy

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


def _call(prompt: str, system: str = SYSTEM_PROMPT, timeout: int = 20, _model: str = None) -> str:
    key = store.get_setting("gemini_api_key", "").strip()
    if not key:
        raise RuntimeError("no_key")
    model = _model or get_model()
    url = ENDPOINT.format(model=model)
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system}]},
        "generationConfig": {"temperature": 0.4},
    }
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        # Modello non trovato/ritirato (es. un nome vecchio salvato): ripiega UNA
        # volta sul modello di default, così l'agente non si rompe da solo.
        if e.code == 404 and _model is None and model != DEFAULT_MODEL:
            return _call(prompt, system, timeout, _model=DEFAULT_MODEL)
        raise
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


# ============================================================================
#  Funzioni dell'agente (Fase 4, parte 2): linguaggio naturale + analisi
# ============================================================================

def _extract_json(txt: str) -> dict:
    """Estrae il primo oggetto JSON da una risposta del modello.

    Tollera i recinti ```json ... ``` e testo prima/dopo: prende dalla prima
    graffa aperta all'ultima chiusa.
    """
    s = (txt or "").strip()
    if s.startswith("```"):
        s = s.strip("`")
        nl = s.find("\n")
        if nl != -1 and s[:nl].strip().lower() in ("json", ""):
            s = s[nl + 1:]
    a, b = s.find("{"), s.rfind("}")
    if a == -1 or b == -1 or b < a:
        raise ValueError("nessun JSON nella risposta")
    return json.loads(s[a:b + 1])


def _match_wallet(nome, wallets):
    """Abbina il nome di portafoglio proposto dall'AI a un wallet reale (id)."""
    n = str(nome or "").strip().lower()
    if not n:
        return None
    for w in wallets:                      # match esatto
        if w.nome.lower() == n:
            return w.id
    for w in wallets:                      # match parziale (es. "carta" -> "Carta di credito")
        if n in w.nome.lower() or w.nome.lower() in n:
            return w.id
    return None


def _norm_date(val, oggi):
    s = str(val or "").strip()[:10]
    return s if re.match(r"^\d{4}-\d{2}-\d{2}$", s) else oggi


def parse_movimento(testo, wallets, categorie, oggi=None) -> dict:
    """Trasforma una frase ('ieri 20€ di benzina con la carta') in una BOZZA di
    movimento da far CONFERMARE all'utente. NON salva nulla.

    Privacy: il testo è ripulito (IBAN/carte/nome) prima di inviarlo all'AI.
    Ritorna un dict 'proposta': {ok, tipo, importo, categoria, wallet_id,
    wallet_to_id, data, data_local, descrizione, confidenza, testo} oppure
    {ok: False, error}.
    """
    if not is_configured():
        return {"ok": False, "error": "no_key"}
    testo = (testo or "").strip()
    if not testo:
        return {"ok": False, "error": "vuoto"}
    oggi = oggi or datetime.utcnow().strftime("%Y-%m-%d")
    nomi_w = [w.nome for w in wallets]
    nomi_c = [c.nome for c in categorie]
    pulito = privacy.scrub_text(testo)
    prompt = (
        "Estrai UN movimento finanziario dalla frase dell'utente e rispondi SOLO "
        "con un oggetto JSON valido, senza testo prima o dopo, con QUESTE chiavi:\n"
        '{"tipo":"uscita|entrata|trasferimento","importo":<numero in euro>,'
        '"categoria":"<breve>","wallet":"<nome o vuoto>","wallet_to":"<nome o vuoto>",'
        '"data":"YYYY-MM-DD","descrizione":"<breve>","confidenza":"bassa|media|alta"}\n'
        f"Oggi è {oggi}. Risolvi le date relative (es. 'ieri', 'lunedì scorso') in data "
        "assoluta; se non è indicata, usa oggi.\n"
        f"Portafogli disponibili (per 'wallet'/'wallet_to' copia il NOME ESATTO più adatto, "
        f"oppure lascia vuoto): {nomi_w}\n"
        f"Categorie già esistenti (riusane una se calza, altrimenti proponine una breve "
        f"e chiara): {nomi_c}\n"
        "'wallet_to' va valorizzato solo per i trasferimenti. Se non è chiaramente un "
        "movimento di denaro, metti importo 0 e confidenza bassa.\n"
        f'Frase: "{pulito}"'
    )
    try:
        raw = _call(prompt, timeout=20)
        data = _extract_json(raw)
    except Exception as e:
        return {"ok": False, "error": type(e).__name__}

    tipo = str(data.get("tipo", "")).lower().strip()
    if tipo not in ("entrata", "uscita", "trasferimento"):
        tipo = "uscita"
    try:
        importo = round(abs(float(str(data.get("importo", 0)).replace(",", "."))), 2)
    except (TypeError, ValueError):
        importo = 0.0
    conf = str(data.get("confidenza", "")).lower()
    conf = "alta" if "alt" in conf else "bassa" if "bass" in conf else "media"
    d = _norm_date(data.get("data"), oggi)
    return {
        "ok": True,
        "tipo": tipo,
        "importo": importo,
        "categoria": str(data.get("categoria", "")).strip()[:120],
        "wallet_id": _match_wallet(data.get("wallet"), wallets),
        "wallet_to_id": _match_wallet(data.get("wallet_to"), wallets) if tipo == "trasferimento" else None,
        "data": d,
        "data_local": d + "T12:00",        # per <input type=datetime-local>
        "descrizione": str(data.get("descrizione", "")).strip()[:200],
        "confidenza": conf,
        "testo": testo,
    }


def analizza_finanze(contesto: str) -> dict:
    """Analisi DESCRITTIVA delle finanze a partire da un riassunto già aggregato
    e anonimo (nessun nome/carta/IBAN). Ritorna {ok, testo} oppure {ok:False, error}.
    """
    if not is_configured():
        return {"ok": False, "error": "no_key"}
    prompt = (
        "Questi sono dati AGGREGATI e anonimi delle finanze personali dell'utente "
        "(nessun dato sensibile). Fai un'analisi DESCRITTIVA in italiano semplice, "
        "3-5 frasi: cosa salta all'occhio, eventuali sbilanciamenti tra le categorie di "
        "spesa, l'andamento entrate/uscite tra i mesi. Vietato dare consigli su cosa "
        "comprare/vendere o su come investire: descrivi soltanto i fatti. Chiudi con una "
        "riga finale 'Confidenza: bassa|media|alta'.\n\n"
        + privacy.scrub_text(contesto)
    )
    try:
        txt = _call(prompt, timeout=25)
    except Exception as e:
        return {"ok": False, "error": type(e).__name__}
    return {"ok": True, "testo": (txt or "").strip()}
