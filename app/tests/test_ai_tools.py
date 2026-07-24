"""Gli strumenti dell'agente e il ciclo che li esegue.

Tre cose da difendere:
1. gli strumenti sono di SOLA LETTURA e l'elenco è chiuso: il modello non può
   inventarne uno né farsi eseguire qualcosa che non abbiamo dichiarato;
2. ogni pagina ha in mano solo gli strumenti che le servono (sulla scheda di un
   titolo non si rovista nei movimenti di casa);
3. il ciclo ha un tetto: l'agente non può girare all'infinito, e se non arriva
   a un testo si ricade su una risposta semplice.
Nessuna rete: la POST al modello è finta.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import shared.ai as ai
import shared.ai_tools as tools


# --------------------------- l'elenco è chiuso ---------------------------
def test_nessuno_strumento_scrive():
    """Se un giorno qualcuno aggiunge qui una funzione che modifica i dati,
    questo test deve accorgersene."""
    vietati = ("salva", "crea", "elimina", "aggiorna", "modifica", "scrivi",
               "imposta", "set_", "cancella", "registra")
    for nome, s in tools.STRUMENTI.items():
        assert not any(v in nome.lower() for v in vietati), nome
        assert not any(v in s["fn"].__name__.lower() for v in vietati), nome


def test_strumento_inesistente_e_un_errore_non_una_fantasia():
    out = tools.esegui("cancella_tutto", {})
    assert "errore" in out and "inesistente" in out["errore"]


def test_argomenti_sbagliati_non_esplodono():
    out = tools.esegui("posizione", {"parametro_che_non_esiste": 1})
    assert "errore" in out


def test_ogni_superficie_ha_solo_i_suoi_attrezzi():
    dash = {d["name"] for d in tools.dichiarazioni("dashboard")}
    titolo = {d["name"] for d in tools.dichiarazioni("titolo")}
    assert "movimenti" in dash                    # sulla dashboard servono
    assert "movimenti" not in titolo              # sulla scheda di un titolo no
    assert "andamento" in titolo
    assert tools.dichiarazioni("pagina_inventata") == []


def test_le_dichiarazioni_hanno_la_forma_che_vuole_gemini():
    for d in tools.dichiarazioni("dashboard"):
        assert set(d) == {"name", "description", "parameters"}
        assert d["parameters"]["type"] == "object"
        assert d["description"]


# --------------------------- il ciclo ---------------------------
def _risposta_testo(txt="Ecco la lettura.\nConfidenza: media"):
    return {"candidates": [{"content": {"role": "model", "parts": [{"text": txt}]}}]}


def _risposta_strumento(nome, args):
    return {"candidates": [{"content": {"role": "model", "parts": [
        {"functionCall": {"name": nome, "args": args}}]}}]}


def test_il_modello_chiede_un_dato_e_lo_riceve(monkeypatch):
    chiamate, eseguiti = [], []

    def finto_post(body, timeout, _model=None):
        chiamate.append(body)
        if len(chiamate) == 1:
            return _risposta_strumento("spese_per_categoria", {"mesi": 3})
        return _risposta_testo()

    monkeypatch.setattr(ai, "_post", finto_post)
    monkeypatch.setattr(tools, "esegui",
                        lambda n, a: eseguiti.append((n, a)) or {"mesi": []})

    out = ai._call("prompt", strumenti=tools.dichiarazioni("finanze"))
    assert "Ecco la lettura." in out
    assert eseguiti == [("spese_per_categoria", {"mesi": 3})]
    # il risultato dello strumento è tornato indietro al modello
    ultimo = chiamate[-1]["contents"][-1]
    assert ultimo["parts"][0]["functionResponse"]["name"] == "spese_per_categoria"


def test_il_ciclo_ha_un_tetto(monkeypatch):
    """Un modello che continua a chiedere strumenti non deve bloccare l'app."""
    giri = {"n": 0}

    def finto_post(body, timeout, _model=None):
        giri["n"] += 1
        if "tools" in body:
            return _risposta_strumento("notizie", {})
        return _risposta_testo("Rispondo con quello che ho.\nConfidenza: bassa")

    monkeypatch.setattr(ai, "_post", finto_post)
    monkeypatch.setattr(tools, "esegui", lambda n, a: {"notizie": []})

    out = ai._call("prompt", strumenti=tools.dichiarazioni("dashboard"))
    assert "Rispondo con quello che ho." in out
    assert giri["n"] == ai.MAX_GIRI_STRUMENTI + 1     # i giri, più quello finale


def test_senza_strumenti_una_sola_chiamata(monkeypatch):
    chiamate = []

    def finto_post(body, timeout, _model=None):
        chiamate.append(body)
        return _risposta_testo()

    monkeypatch.setattr(ai, "_post", finto_post)
    ai._call("prompt")
    assert len(chiamate) == 1 and "tools" not in chiamate[0]


def test_gli_strumenti_arrivano_al_modello(monkeypatch):
    visto = {}
    monkeypatch.setattr(ai, "_post",
                        lambda body, t, _model=None: visto.setdefault("b", body) and None
                        or _risposta_testo())
    monkeypatch.setattr(ai, "is_configured", lambda: True)
    ai._genera("titolo", contesto="ETF globale")
    nomi = {d["name"] for d in visto["b"]["tools"][0]["functionDeclarations"]}
    assert nomi == set(tools.PER_SUPERFICIE["titolo"])
