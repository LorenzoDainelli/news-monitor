"""Sezione Notizie: mostra solo ciò che è arrivato per email.

Dalla Fase 0 il robot registra in `predictions.json` anche i candidati **non
inviati** (`inviata: false`), che gli servono come storico per verificare a
posteriori le proprie stime. Quelli NON devono comparire nell'app, altrimenti la
sezione si riempie di notizie marginali.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from news import reader  # noqa: E402


def _voce(id_, inviata=None, rilevanza=70):
    it = {"id": id_, "ticker": "AAPL", "titolo": id_, "data": "2026-07-20",
          "rilevanza": rilevanza, "confidenza": "media", "url": f"http://x/{id_}",
          "impatto": {"breve": "positivo", "medio": "neutro", "lungo": "neutro"}}
    if inviata is not None:
        it["inviata"] = inviata
    return it


def test_le_non_inviate_non_si_vedono(monkeypatch):
    voci = [_voce("inviata", True), _voce("non-inviata", False)]
    monkeypatch.setattr(reader, "_read_items", lambda p: voci if "predictions" in str(p).lower() else [])
    titoli = [c["titolo"] for c in reader.news_cards()]
    assert titoli == ["inviata"]


def test_voci_vecchie_senza_il_campo_restano_visibili(monkeypatch):
    """Retrocompatibilità: prima della Fase 0 si registravano solo le inviate."""
    voci = [_voce("storica")]                      # nessun campo 'inviata'
    monkeypatch.setattr(reader, "_read_items", lambda p: voci if "predictions" in str(p).lower() else [])
    assert [c["titolo"] for c in reader.news_cards()] == ["storica"]


def test_la_data_aggiornato_ignora_le_non_inviate(monkeypatch):
    """L'etichetta 'aggiornato' non deve riferirsi a una notizia che non si vede."""
    vecchia = _voce("inviata", True)
    nuova = _voce("non-inviata", False)
    nuova["data"] = "2026-07-25"
    monkeypatch.setattr(reader, "_read_items",
                        lambda p: [vecchia, nuova] if "predictions" in str(p).lower() else [])
    assert reader.latest_date() == "20/07/2026"
