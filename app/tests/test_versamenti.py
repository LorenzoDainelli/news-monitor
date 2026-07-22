"""Test del motore dei versamenti PAC (portfolio/versamenti.py).

Verifica: ripartizione per % (normalizzata, totale esatto), accumulo PMC sulle
quantità, esclusione di un titolo, e annullamento esatto con elimina().
I prezzi sono STUBBATI (nessuna rete): il test guarda la logica, non i mercati.
"""
import sys
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.db import Base
from portfolio.models import Position, Versamento, VersamentoRiga
import portfolio.service as pf_service
import portfolio.versamenti as versamenti


@pytest.fixture(autouse=True)
def test_db(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path/'test.db'}",
                           connect_args={"check_same_thread": False})
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    import shared.db as db_mod
    monkeypatch.setattr(db_mod, "SessionLocal", TestSession)
    monkeypatch.setattr(pf_service, "SessionLocal", TestSession)
    monkeypatch.setattr(versamenti, "SessionLocal", TestSession)
    # niente rete: prezzo fisso 10€ per tutti, e nessuna quotazione in cache
    monkeypatch.setattr(versamenti.market, "quotes_map", lambda: {})
    monkeypatch.setattr(versamenti, "_prezzo_eur_alla_data",
                        lambda p, data, qmap, oggi: (10.0, "test"))
    yield TestSession


def _seed(Session):
    """3 titoli con % 50/30/20 (somma 100)."""
    with Session() as db:
        db.add_all([
            Position(nome="Alpha", ticker="A", pct_target=50.0, ordine=0),
            Position(nome="Beta", ticker="B", pct_target=30.0, ordine=1),
            Position(nome="Gamma", ticker="C", pct_target=20.0, ordine=2),
        ])
        db.commit()
        return {p.ticker: p.id for p in db.execute(select(Position)).scalars()}


def _pos(Session, pid):
    with Session() as db:
        return db.get(Position, pid)


def test_riparto_e_accumulo_pmc(test_db):
    Session = test_db
    ids = _seed(Session)
    vid = versamenti.salva(100.0, date.today(), "TR", esclusi=set())
    assert vid is not None

    a, b, c = _pos(Session, ids["A"]), _pos(Session, ids["B"]), _pos(Session, ids["C"])
    # €50/€30/€20 a prezzo 10 -> 5/3/2 quote; versato = gli euro
    assert (a.versato_totale, b.versato_totale, c.versato_totale) == (50.0, 30.0, 20.0)
    assert (round(a.quantita, 6), round(b.quantita, 6), round(c.quantita, 6)) == (5.0, 3.0, 2.0)

    # secondo PAC identico: le quantità si SOMMANO (una sola posizione, PMC)
    versamenti.salva(100.0, date.today(), "TR", esclusi=set())
    a2 = _pos(Session, ids["A"])
    assert round(a2.quantita, 6) == 10.0 and a2.versato_totale == 100.0

    # due versamenti a storico
    with Session() as db:
        assert db.execute(select(Versamento)).scalars().all().__len__() == 2
        assert db.execute(select(VersamentoRiga)).scalars().all().__len__() == 6


def test_esclusione_ridistribuisce(test_db):
    Session = test_db
    ids = _seed(Session)
    # escludo Gamma: l'importo si ridistribuisce fra A(50) e B(30) -> 62.5 / 37.5
    versamenti.salva(100.0, date.today(), "TR", esclusi={ids["C"]})
    a, b, c = _pos(Session, ids["A"]), _pos(Session, ids["B"]), _pos(Session, ids["C"])
    assert round(a.versato_totale + b.versato_totale, 2) == 100.0
    assert round(a.versato_totale, 2) == 62.5 and round(b.versato_totale, 2) == 37.5
    assert (c.quantita in (None, 0)) and c.versato_totale == 0.0


def test_totale_esatto_con_arrotondamenti(test_db):
    Session = test_db
    # % che non dividono bene 100 (33.33/33.33/33.34-ish): il totale deve tornare esatto
    with Session() as db:
        db.add_all([
            Position(nome="X", ticker="X", pct_target=33.0, ordine=0),
            Position(nome="Y", ticker="Y", pct_target=33.0, ordine=1),
            Position(nome="Z", ticker="Z", pct_target=34.0, ordine=2),
        ])
        db.commit()
    versamenti.salva(100.0, date.today(), "TR", esclusi=set())
    with Session() as db:
        tot = sum(p.versato_totale for p in db.execute(select(Position)).scalars())
    assert round(tot, 2) == 100.0


def test_elimina_ripristina(test_db):
    Session = test_db
    ids = _seed(Session)
    vid = versamenti.salva(100.0, date.today(), "TR", esclusi=set())
    assert versamenti.elimina(vid) is True

    a, b, c = _pos(Session, ids["A"]), _pos(Session, ids["B"]), _pos(Session, ids["C"])
    assert (a.quantita, b.quantita, c.quantita) == (0.0, 0.0, 0.0)
    assert (a.versato_totale, b.versato_totale, c.versato_totale) == (0.0, 0.0, 0.0)
    with Session() as db:
        assert db.execute(select(Versamento)).scalars().first() is None
        assert db.execute(select(VersamentoRiga)).scalars().first() is None
