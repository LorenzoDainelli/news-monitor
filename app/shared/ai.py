"""Agente AI condiviso — fondamenta (Fase 4, parte 1).

Qui c'è solo lo STRATO DI BASE: connessione a Gemini, prova connessione, modello
configurabile e l'interruttore doppia modalità. Le funzioni che mandano dati
(inserimento spese in linguaggio naturale, analisi) e il filtro privacy per sezione
sono più sotto in questo modulo.

Filosofia dell'agente (dal CLAUDE.md del news-monitor):
- mai segnali operativi (compra/vendi/entra/esci);
- non è un oracolo: non prevede i prezzi; ogni stima ha un livello di confidenza
  dichiarato (bassa/media/alta) e un disclaimer;
- italiano semplice, onestà intellettuale, ridurre il rumore;
- la decisione finale resta sempre dell'utente.

Provider ASTRATTO per lo stesso modello Gemini, scelto in Impostazioni: "studio"
(Google AI Studio, chiave API, piano gratuito — default) oppure "vertex" (Vertex
AI su Google Cloud, service account — consuma i crediti del progetto). La chiave/
credenziali stanno solo in locale (database), mai nei log né nell'URL (via header).
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

# Due strade per lo STESSO modello Gemini, scelte dall'utente in Impostazioni:
#  - "studio": Google AI Studio, chiave API, piano gratuito → DEFAULT, invariato;
#  - "vertex": Vertex AI su Google Cloud, autenticazione con service account →
#    consuma i crediti del progetto Cloud dell'utente. Il CORPO della richiesta
#    (contents/systemInstruction/generationConfig) è identico: cambiano solo
#    l'endpoint e l'header di autenticazione. Guida in docs/SETUP-VERTEX.md.
PROVIDER_STUDIO = "studio"
PROVIDER_VERTEX = "vertex"
PROVIDERS = (PROVIDER_STUDIO, PROVIDER_VERTEX)
STUDIO_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_VERTEX_LOCATION = "global"        # endpoint 'global': ampia disponibilità dei modelli
VERTEX_SCOPE = "https://www.googleapis.com/auth/cloud-platform"

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


def get_provider() -> str:
    p = store.get_setting("ai_provider", PROVIDER_STUDIO).strip().lower()
    return p if p in PROVIDERS else PROVIDER_STUDIO


def set_provider(value: str) -> None:
    v = (value or "").strip().lower()
    if v in PROVIDERS:
        store.set_setting("ai_provider", v)


def vertex_conf() -> dict:
    """Configurazione Vertex (progetto/regione/service account) dal DB locale.
    Il JSON del service account è un SEGRETO: mai stamparlo né loggarlo."""
    return {
        "project": store.get_setting("vertex_project", "").strip(),
        "location": store.get_setting("vertex_location", "").strip() or DEFAULT_VERTEX_LOCATION,
        "sa_json": store.get_setting("vertex_service_account_json", "").strip(),
    }


def is_configured() -> bool:
    """True se il provider scelto è pronto all'uso (l'agente è sbloccato)."""
    if get_provider() == PROVIDER_VERTEX:
        c = vertex_conf()
        return bool(c["project"] and c["sa_json"])
    return store.has_key("gemini_api_key")


# Credenziali Vertex in cache: google-auth gestisce il refresh del token (~1h),
# così non rifirmiamo il JWT a ogni chiamata. La cache si invalida da sola se
# cambia il service account (impronta del JSON).
_vertex_cache = {"fp": None, "creds": None}


def _vertex_access_token() -> str:
    c = vertex_conf()
    if not c["project"] or not c["sa_json"]:
        raise RuntimeError("no_key")
    try:
        from google.oauth2 import service_account
        import google.auth.transport.requests as _gart
    except ImportError as e:
        # Provider Vertex scelto ma le librerie non sono installate (vedi requirements).
        raise RuntimeError("vertex_libs_mancanti") from e
    import hashlib
    fp = hashlib.sha256(c["sa_json"].encode("utf-8")).hexdigest()
    if _vertex_cache["fp"] != fp:
        info = json.loads(c["sa_json"])
        _vertex_cache["creds"] = service_account.Credentials.from_service_account_info(
            info, scopes=[VERTEX_SCOPE])
        _vertex_cache["fp"] = fp
    creds = _vertex_cache["creds"]
    if not creds.valid:
        creds.refresh(_gart.Request())
    return creds.token


def _vertex_endpoint(model: str) -> str:
    c = vertex_conf()
    loc = c["location"]
    host = "aiplatform.googleapis.com" if loc == "global" else loc + "-aiplatform.googleapis.com"
    return ("https://" + host + "/v1/projects/" + c["project"] +
            "/locations/" + loc + "/publishers/google/models/" + model + ":generateContent")


def _endpoint_headers(model: str) -> tuple:
    """(url, headers) per il provider corrente. Chiave/token sempre negli header,
    MAI nell'URL."""
    if get_provider() == PROVIDER_VERTEX:
        token = _vertex_access_token()
        return _vertex_endpoint(model), {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
        }
    key = store.get_setting("gemini_api_key", "").strip()
    if not key:
        raise RuntimeError("no_key")
    return STUDIO_ENDPOINT.format(model=model), {
        "Content-Type": "application/json",
        "x-goog-api-key": key,
    }


def _call(prompt: str, system: str = SYSTEM_PROMPT, timeout: int = 20, _model: str = None) -> str:
    model = _model or get_model()
    url, headers = _endpoint_headers(model)
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system}]},
        "generationConfig": {"temperature": 0.4},
    }
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        # Modello non trovato/ritirato (es. un nome vecchio salvato): ripiega UNA
        # volta sul modello di default, così l'agente non si rompe da solo.
        if e.code == 404 and _model is None and model != DEFAULT_MODEL:
            return _call(prompt, system, timeout, _model=DEFAULT_MODEL)
        # Limiti del free tier esauriti sul principale: UNA prova col ripiego lite.
        if e.code == 429 and _model is None and model != DEFAULT_FALLBACK:
            return _call(prompt, system, timeout, _model=DEFAULT_FALLBACK)
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
    except RuntimeError as e:
        return (False, str(e))          # es. "vertex_libs_mancanti", "no_key"
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
    oggi = oggi or datetime.now().strftime("%Y-%m-%d")  # data LOCALE: 'ieri' giusto anche di sera
    nomi_w = [w.nome for w in wallets]
    nomi_c = [c.nome for c in categorie]
    pulito = privacy.scrub_text(testo)
    prompt = (
        "Estrai UN movimento finanziario dalla frase dell'utente e rispondi SOLO "
        "con un oggetto JSON valido, senza testo prima o dopo, con QUESTE chiavi:\n"
        '{"tipo":"uscita|entrata|trasferimento|giro","importo":<numero in euro>,'
        '"categoria":"<breve>","wallet":"<nome o vuoto>","wallet_to":"<nome o vuoto>",'
        '"data":"YYYY-MM-DD","descrizione":"<breve>","confidenza":"bassa|media|alta",'
        '"controparte":"<chi rimborsa, o vuoto>","importo_ricevuto":<numero o 0>,'
        '"data_ricevuto":"YYYY-MM-DD o vuoto","wallet_ricevuto":"<nome o vuoto>"}\n'
        f"Oggi è {oggi}. Risolvi le date relative (es. 'ieri', 'lunedì scorso') in data "
        "assoluta; se non è indicata, usa oggi.\n"
        f"Portafogli disponibili (per 'wallet'/'wallet_to'/'wallet_ricevuto' copia il NOME "
        f"ESATTO più adatto, oppure lascia vuoto): {nomi_w}\n"
        f"Categorie già esistenti (riusane una se calza, altrimenti proponine una breve "
        f"e chiara): {nomi_c}\n"
        "'wallet_to' va valorizzato solo per i trasferimenti.\n"
        "tipo 'giro' = spesa che qualcuno rimborsa (es. 'la pagano i miei', 'me li ridà "
        "il babbo'): 'importo' è quanto speso; in 'controparte' metti chi rimborsa; se la "
        "frase dice anche quanto è stato ridato compila 'importo_ricevuto' (e "
        "'data_ricevuto'/'wallet_ricevuto' se indicati), altrimenti lascia 0 (rimborso in "
        "arrivo). Le chiavi 'controparte'/'importo_ricevuto'/'data_ricevuto'/"
        "'wallet_ricevuto' restano vuote/0 per gli altri tipi.\n"
        "Se non è chiaramente un movimento di denaro, metti importo 0 e confidenza bassa.\n"
        f'Frase: "{pulito}"'
    )
    try:
        raw = _call(prompt, timeout=20)
        data = _extract_json(raw)
    except Exception as e:
        return {"ok": False, "error": type(e).__name__}

    tipo = str(data.get("tipo", "")).lower().strip()
    if tipo not in ("entrata", "uscita", "trasferimento", "giro"):
        tipo = "uscita"

    def _num(val):
        try:
            return round(abs(float(str(val or 0).replace(",", "."))), 2)
        except (TypeError, ValueError):
            return 0.0

    importo = _num(data.get("importo"))
    conf = str(data.get("confidenza", "")).lower()
    conf = "alta" if "alt" in conf else "bassa" if "bass" in conf else "media"
    d = _norm_date(data.get("data"), oggi)
    # partita di giro: gamba del rimborso (0/vuoto = partita APERTA, arriverà dopo)
    ricevuto = _num(data.get("importo_ricevuto")) if tipo == "giro" else 0.0
    d_ric = _norm_date(data.get("data_ricevuto"), oggi) if ricevuto else None
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
        "controparte": str(data.get("controparte", "")).strip()[:80] if tipo == "giro" else "",
        "importo_ricevuto": ricevuto if (tipo == "giro" and ricevuto) else None,
        "data_ricevuto_local": (d_ric + "T12:00") if d_ric else None,
        "wallet_ricevuto_id": _match_wallet(data.get("wallet_ricevuto"), wallets) if (tipo == "giro" and ricevuto) else None,
    }


def _estrai_confidenza(txt: str) -> tuple[str, str]:
    """Separa la riga finale 'Confidenza: X' dal testo. Ritorna (testo, conf)."""
    righe = [r for r in (txt or "").strip().splitlines() if r.strip()]
    conf = "media"
    if righe:
        ultima = righe[-1].strip().lower()
        m = re.search(r"confidenza\s*[:\-]?\s*(bassa|media|alta)", ultima)
        if m:
            conf = m.group(1)
            righe = righe[:-1]
    return "\n".join(righe).strip(), conf


def punto_settimana(contesto: str) -> dict:
    """'Il punto della settimana' per la dashboard: 2-4 frasi descrittive su dati
    aggregati e anonimi. Ritorna {ok, text, conf} oppure {ok: False, error}."""
    if not is_configured():
        return {"ok": False, "error": "no_key"}
    prompt = (
        "Questi sono dati AGGREGATI e anonimi (nessun dato sensibile) della situazione "
        "finanziaria dell'utente. Scrivi 'il punto della settimana' in italiano semplice, "
        "2-4 frasi DESCRITTIVE: cosa salta all'occhio su liquidità, spese e composizione "
        "del portafoglio. Vietato ogni consiglio operativo (comprare/vendere/spostare "
        "soldi): descrivi soltanto i fatti. Chiudi con una riga 'Confidenza: bassa|media|alta'.\n\n"
        + privacy.scrub_text(contesto)
    )
    try:
        txt = _call(prompt, timeout=25)
    except Exception as e:
        return {"ok": False, "error": type(e).__name__}
    testo, conf = _estrai_confidenza(txt)
    return {"ok": True, "text": testo, "conf": conf}


def analizza_posizione(descr: str) -> dict:
    """'Cosa ne pensa l'agente' su un singolo titolo/ETF, SOLO da dati pubblici
    (nome, tipo, categoria, settori, performance): mai valori posseduti, quantità
    o ISIN. Ritorna {ok, text, conf} oppure {ok: False, error}."""
    if not is_configured():
        return {"ok": False, "error": "no_key"}
    prompt = (
        "Descrivi in italiano semplice (3-4 frasi) le caratteristiche di questo "
        "strumento in un portafoglio diversificato: cosa lo muove, a quali settori/"
        "rischi è esposto, che ruolo tipicamente ricopre. SOLO fatti qualitativi e "
        "pubblici: niente previsioni di prezzo, niente consigli operativi "
        "(comprare/vendere), niente numeri inventati. Chiudi con una riga "
        "'Confidenza: bassa|media|alta'.\n\n" + privacy.scrub_text(descr)
    )
    try:
        txt = _call(prompt, timeout=25)
    except Exception as e:
        return {"ok": False, "error": type(e).__name__}
    testo, conf = _estrai_confidenza(txt)
    return {"ok": True, "text": testo, "conf": conf}


def spiega_metrica(label: str, valore: str, contesto: str = "") -> dict:
    """Spiega una singola metrica dell'analisi (popup ✨ della pagina Analisi).
    Ritorna {ok, text, conf} oppure {ok: False, error}."""
    if not is_configured():
        return {"ok": False, "error": "no_key"}
    prompt = (
        (privacy.scrub_text(contesto) + "\n\n" if contesto else "")
        + "Spiega in 3-4 frasi, in italiano semplice, cosa significa questo dato "
        f"per il portafoglio: \"{privacy.scrub_text(label)} = {privacy.scrub_text(valore)}\". "
        "Tono neutro e descrittivo, niente consigli operativi (comprare/vendere), "
        "niente numeri inventati. Chiudi con una riga 'Confidenza: bassa|media|alta'."
    )
    try:
        txt = _call(prompt, timeout=25)
    except Exception as e:
        return {"ok": False, "error": type(e).__name__}
    testo, conf = _estrai_confidenza(txt)
    return {"ok": True, "text": testo, "conf": conf}


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
    testo, conf = _estrai_confidenza(txt)
    return {"ok": True, "text": testo, "conf": conf, "testo": testo}
