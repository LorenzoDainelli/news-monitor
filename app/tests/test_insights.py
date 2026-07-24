"""L'estrattore di fatti e il montaggio del prompt per superficie.

Due cose vanno difese, perché sono l'anima del nuovo agente:
1. i fatti nascono da un confronto con la STORIA dell'utente e hanno delle
   SOGLIE: sotto quelle non sono fatti, sono rumore;
2. se non c'è niente di notevole, il prompt deve dirlo esplicitamente al modello,
   invece di lasciarlo libero di inventare significato.
Nessuna rete: la chiamata al modello è finta.
"""
import sys
from datetime import date, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared import insights
import shared.ai as ai


# --------------------------- l'estrattore ---------------------------
def _riepiloghi(monkeypatch, per_mese: dict, movimenti=None):
    """Finge lo storico mensile: {(anno, mese): {entrate, uscite, categorie{}}}."""
    def finto(anno, mese):
        d = per_mese.get((anno, mese), {})
        spese = [{"nome": n, "tot": t} for n, t in sorted(
            d.get("categorie", {}).items(), key=lambda x: -x[1])]
        return {"entrate": d.get("entrate", 0.0), "uscite": d.get("uscite", 0.0),
                "saldo": d.get("entrate", 0.0) - d.get("uscite", 0.0),
                "spese_categoria": spese, "anno": anno, "mese": mese}

    import finance.service as fin
    monkeypatch.setattr(fin, "riepilogo_mese", finto)
    monkeypatch.setattr(fin, "lista_movimenti", lambda **k: movimenti or [])


def test_categoria_sopra_la_propria_mediana(monkeypatch):
    _riepiloghi(monkeypatch, {
        (2026, 7): {"uscite": 100.0, "categorie": {"Abbonamenti": 47.0}},
        (2026, 6): {"uscite": 90.0, "categorie": {"Abbonamenti": 22.0}},
        (2026, 5): {"uscite": 88.0, "categorie": {"Abbonamenti": 22.0}},
        (2026, 4): {"uscite": 92.0, "categorie": {"Abbonamenti": 20.0}},
    })
    f = insights.fatti_finanze(oggi=datetime(2026, 7, 20))
    sopra = [x for x in f if x.chiave == "cat:abbonamenti:sopra"]
    assert sopra, "lo scostamento oltre soglia deve produrre un fatto"
    assert "22,00 €" in sopra[0].testo and "47,00 €" in sopra[0].testo
    assert sopra[0].dati["mediana"] == 22.0


def test_sotto_soglia_non_e_un_fatto(monkeypatch):
    """Piccoli scostamenti e piccoli importi NON devono generare rumore."""
    _riepiloghi(monkeypatch, {
        (2026, 7): {"uscite": 100.0, "categorie": {"Bar": 24.0, "Briciole": 90.0}},
        (2026, 6): {"uscite": 100.0, "categorie": {"Bar": 22.0, "Briciole": 3.0}},
        (2026, 5): {"uscite": 100.0, "categorie": {"Bar": 21.0, "Briciole": 3.0}},
    })
    chiavi = [x.chiave for x in insights.fatti_finanze(oggi=datetime(2026, 7, 20))]
    assert "cat:bar:sopra" not in chiavi        # +9%: sotto MIN_SCOSTAMENTO
    assert "cat:briciole:sopra" in chiavi       # +2900% su 90 €: quello sì


def test_abitudine_sparita(monkeypatch):
    _riepiloghi(monkeypatch, {
        (2026, 7): {"uscite": 50.0, "categorie": {"Spesa": 50.0}},
        (2026, 6): {"uscite": 80.0, "categorie": {"Spesa": 50.0, "Palestra": 30.0}},
        (2026, 5): {"uscite": 80.0, "categorie": {"Spesa": 50.0, "Palestra": 30.0}},
        (2026, 4): {"uscite": 80.0, "categorie": {"Spesa": 50.0, "Palestra": 30.0}},
    })
    f = {x.chiave: x for x in insights.fatti_finanze(oggi=datetime(2026, 7, 20))}
    assert "cat:palestra:sparita" in f
    assert "3" in f["cat:palestra:sparita"].testo      # presente in 3 mesi


def test_niente_storia_niente_fatti(monkeypatch):
    """Con un mese solo di dati non esiste ancora un'abitudine: nessun confronto."""
    _riepiloghi(monkeypatch, {(2026, 7): {"uscite": 500.0, "categorie": {"Viaggi": 500.0}}})
    chiavi = [x.chiave for x in insights.fatti_finanze(oggi=datetime(2026, 7, 20))]
    assert not any(c.startswith("cat:viaggi:sopra") for c in chiavi)


def test_numeri_all_italiana():
    assert insights._eur(1234.5) == "1.234,50 €"
    assert insights._pct(36.9, 1) == "36,9%"
    assert insights._pct(4.2, 1, segno=True) == "+4,2%"


def test_ordinati_per_forza(monkeypatch):
    _riepiloghi(monkeypatch, {
        (2026, 7): {"uscite": 600.0, "categorie": {"Viaggi": 500.0, "Libri": 30.0}},
        (2026, 6): {"uscite": 120.0, "categorie": {"Viaggi": 100.0, "Libri": 20.0}},
        (2026, 5): {"uscite": 120.0, "categorie": {"Viaggi": 100.0, "Libri": 20.0}},
    })
    f = insights.fatti_finanze(oggi=datetime(2026, 7, 20))
    f.sort(key=lambda x: x.forza, reverse=True)
    assert f[0].dati.get("categoria") == "Viaggi"   # 500 € batte 30 €


# --------------------------- il prompt ---------------------------
def _cattura_prompt(monkeypatch):
    visto = {}

    def finto_call(prompt, system=ai.SYSTEM_PROMPT, timeout=20, _model=None):
        visto["prompt"] = prompt
        visto["system"] = system
        return "Testo di prova.\nConfidenza: media"

    monkeypatch.setattr(ai, "_call", finto_call)
    monkeypatch.setattr(ai, "is_configured", lambda: True)
    return visto


def test_i_fatti_finiscono_nel_prompt(monkeypatch):
    visto = _cattura_prompt(monkeypatch)
    fatti = [insights.Fatto(chiave="k", testo="Gli abbonamenti sono raddoppiati.",
                            forza=80.0)]
    res = ai._genera("dashboard", fatti=fatti)
    assert res["ok"] and res["conf"] == "media"
    assert "Gli abbonamenti sono raddoppiati." in visto["prompt"]
    assert "NON ricalcolare" in visto["prompt"]


def test_senza_fatti_il_prompt_ordina_di_tacere(monkeypatch):
    visto = _cattura_prompt(monkeypatch)
    ai._genera("dashboard", fatti=[])
    assert "NESSUN FATTO NOTEVOLE" in visto["prompt"]
    assert "NON cercare comunque qualcosa da" in visto["prompt"]


def test_ogni_superficie_ha_il_suo_registro(monkeypatch):
    visto = _cattura_prompt(monkeypatch)
    ai._genera("titolo")
    titolo = visto["prompt"]
    ai._genera("metrica")
    metrica = visto["prompt"]
    assert "divulgatore" in titolo and "traduttore" in metrica
    assert titolo != metrica


def test_le_regole_anti_piattume_sono_nel_system(monkeypatch):
    visto = _cattura_prompt(monkeypatch)
    ai._genera("dashboard")
    sistema = visto["system"]
    assert "APRI DAL FATTO PIÙ FORTE" in sistema
    assert "NON INVENTARE MAI NUMERI" in sistema
    assert "MAI segnali operativi" in sistema        # la regola di sempre resta


def test_senza_chiave_non_chiama_il_modello(monkeypatch):
    monkeypatch.setattr(ai, "is_configured", lambda: False)
    assert ai._genera("dashboard")["error"] == "no_key"
