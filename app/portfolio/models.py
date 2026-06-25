"""Tabella delle posizioni del portafoglio.

Una 'posizione' = un titolo che vuoi seguire (ETF o azione) con la sua quota
target. I campi di mercato (prezzo, ecc.) NON stanno qui: arriveranno in Fase 2
in tabelle separate, così i tuoi dati restano puliti e mai 'inventati'.
"""
from datetime import date

from sqlalchemy import String, Float, Integer, Date, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.db import Base

TIPO_ETF = "ETF"
TIPO_AZIONE = "Azione"


class Position(Base):
    __tablename__ = "portfolio_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # --- anagrafica (inserita/modificata da te dall'interfaccia) ---
    nome: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(20), default=TIPO_AZIONE)   # ETF | Azione
    categoria: Mapped[str] = mapped_column(String(120), default="")      # tema/settore
    ticker: Mapped[str] = mapped_column(String(30), default="")
    isin: Mapped[str] = mapped_column(String(20), default="")

    # --- allocazione ---
    # Quota target in %. Per i titoli a importo fisso (Take-Two) resta 0 e si usa
    # importo_fisso: l'app mostra a parte la % implicita.
    pct_target: Mapped[float] = mapped_column(Float, default=0.0)
    importo_fisso: Mapped[float | None] = mapped_column(Float, nullable=True)

    # --- quanto possiedi davvero (lo riempi tu, può restare vuoto) ---
    quantita: Mapped[float | None] = mapped_column(Float, nullable=True)
    valore_posseduto: Mapped[float | None] = mapped_column(Float, nullable=True)  # in €
    data_ultimo_acquisto: Mapped[date | None] = mapped_column(Date, nullable=True)

    note: Mapped[str] = mapped_column(Text, default="")
    ordine: Mapped[int] = mapped_column(Integer, default=0)  # ordine di visualizzazione

    @property
    def is_fisso(self) -> bool:
        return self.importo_fisso is not None
