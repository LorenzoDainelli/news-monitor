"""Il PAC riflesso in Finanze: trasferimento automatico + conto a saldo derivato.

Due regole da difendere:
1. ogni versamento PAC genera UN solo trasferimento (conto scelto -> "PAC
   investimenti"), che si aggiorna con la modifica e sparisce con l'eliminazione;
2. il saldo del conto PAC è quello VIVO del Portafoglio (versato + rivalutazione),
   e le oscillazioni NON diventano mai movimenti.
Nessuna rete: prezzi e vista del portafoglio sono stubbati.
"""
import sys
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.db import Base
from portfolio.models import Position, Versamento
from finance.models import Wallet, Transaction, TIPO_TRASFERIMENTO
import shared.settings_store  # noqa: F401  (registra shared_settings, usata dal sync)
import shared.sync            # noqa: F401  (importalo PRIMA del primo flush, come fa main.py)
import portfolio.service as pf_service
import portfolio.versamenti as versamenti
import finance.service as fin_service


@pytest.fixture(autouse=True)
def test_db(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path/'test.db'}",
                           connect_args={"check_same_thread": False})
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    import shared.db as db_mod
    for mod in (db_mod, pf_service, versamenti, fin_service):
        monkeypatch.setattr(mod, "SessionLocal", TestSession)
    monkeypatch.setattr(versamenti.market, "quotes_map", lambda: {})
    monkeypatch.setattr(versamenti, "_prezzo_eur_alla_data",
                        lambda p, data, qmap, oggi, ora="": (10.0, "test"))

    with TestSession() as db:
        db.add_all([
            Wallet(nome="Trade Republic", tipo="carta", ordine=0),
            Wallet(nome=fin_service.NOME_WALLET_PAC, tipo="investimento", ordine=1),
            Position(nome="Alpha", ticker="A", pct_target=50.0, ordine=0),
            Position(nome="Beta", ticker="B", pct_target=50.0, ordine=1),
        ])
        db.commit()
    yield TestSession


def _movimenti(Session):
    with Session() as db:
        return list(db.execute(select(Transaction).where(
            Transaction.deleted.is_(False))).scalars().all())


def test_pac_crea_un_solo_trasferimento(test_db):
    Session = test_db
    vid = versamenti.salva(100.0, date.today(), "Trade Republic", esclusi=set())

    movs = _movimenti(Session)
    assert len(movs) == 1
    t = movs[0]
    assert t.tipo == TIPO_TRASFERIMENTO and t.importo == 100.0
    src = fin_service.wallet_per_nome("Trade Republic")
    dest = fin_service.wallet_per_nome(fin_service.NOME_WALLET_PAC)
    assert (t.wallet_id, t.wallet_to_id) == (src.id, dest.id)
    with Session() as db:
        assert db.get(Versamento, vid).tx_id == t.id


def test_modifica_aggiorna_lo_stesso_movimento(test_db):
    Session = test_db
    vid = versamenti.salva(100.0, date.today(), "Trade Republic", esclusi=set())
    tx_prima = _movimenti(Session)[0].id

    versamenti.salva(150.0, date.today(), "Trade Republic", esclusi=set(), vid=vid)
    movs = _movimenti(Session)
    assert len(movs) == 1                      # non si duplica
    assert movs[0].id == tx_prima and movs[0].importo == 150.0


def test_elimina_toglie_anche_il_movimento(test_db):
    Session = test_db
    vid = versamenti.salva(100.0, date.today(), "Trade Republic", esclusi=set())
    assert versamenti.elimina(vid) is True
    assert _movimenti(Session) == []


def test_conto_pac_ha_saldo_vivo_dal_portafoglio(test_db, monkeypatch):
    Session = test_db
    versamenti.salva(100.0, date.today(), "Trade Republic", esclusi=set())

    # il Portafoglio vale 100,42 € (mercato salito): il conto PAC deve seguirlo,
    # SENZA che nasca un movimento per i 42 centesimi.
    def finta_vista():
        with Session() as db:
            righe = [{"p": p} for p in db.execute(select(Position)).scalars().all()]
        return {"righe": righe, "totale": 100.42, "ha_totale": True}

    monkeypatch.setattr(pf_service, "vista_portafoglio", finta_vista)

    res = fin_service.saldi()
    pac = next(r for r in res["righe"]
               if r["w"].nome == fin_service.NOME_WALLET_PAC)
    assert pac["derivato"] is True
    assert (pac["saldo"], pac["versato"], pac["rivalutazione"]) == (100.42, 100.0, 0.42)
    # il trasferimento resta UNO: la rivalutazione non è un movimento
    assert len(_movimenti(Session)) == 1
    # e il conto di partenza è sceso di 100
    tr = next(r for r in res["righe"] if r["w"].nome == "Trade Republic")
    assert tr["saldo"] == -100.0


def test_senza_prezzi_il_saldo_resta_quello_dei_movimenti(test_db, monkeypatch):
    Session = test_db
    versamenti.salva(100.0, date.today(), "Trade Republic", esclusi=set())
    monkeypatch.setattr(pf_service, "vista_portafoglio",
                        lambda: {"righe": [], "totale": 0.0, "ha_totale": False})
    pac = next(r for r in fin_service.saldi()["righe"]
               if r["w"].nome == fin_service.NOME_WALLET_PAC)
    assert pac["saldo"] == 100.0 and "derivato" not in pac   # niente valori inventati
