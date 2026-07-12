"""Tabelle delle finanze personali: portafogli (conti/wallet), categorie, movimenti.

Quattro tipi di movimento:
- entrata        -> aumenta il saldo del wallet
- uscita         -> diminuisce il saldo del wallet
- trasferimento  -> sposta denaro da un wallet all'altro (NON cambia il patrimonio
                    totale, cambia solo i due saldi)
- giro           -> "partita di giro": spesa che qualcuno rimborsa (es. la pagano
                    i genitori). Una sola riga con DUE gambe: quella spesa
                    (importo/data/wallet_id) e quella ricevuta (importo_ricevuto/
                    data_ricevuto/wallet_to_id). I saldi si muovono davvero, ma
                    nelle statistiche entrate/uscite conta SOLO la differenza:
                    ricevuto > speso = entrata (alla data del rimborso),
                    ricevuto < speso = uscita (alla data della spesa).
                    Gamba ricevuta assente (importo_ricevuto NULL) = partita
                    APERTA, "in attesa di rimborso": neutra finché non si chiude.

Prefisso tabelle 'finance_' per non interferire col modulo portafoglio.
"""
from datetime import datetime

from sqlalchemy import String, Float, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from shared.db import Base

TIPO_ENTRATA = "entrata"
TIPO_USCITA = "uscita"
TIPO_TRASFERIMENTO = "trasferimento"
TIPO_GIRO = "giro"                     # partita di giro (spesa rimborsata)
TIPI_MOVIMENTO = (TIPO_ENTRATA, TIPO_USCITA, TIPO_TRASFERIMENTO, TIPO_GIRO)

# Tipi di wallet (per etichetta/icona); valori liberi, questi sono i noti.
TIPI_WALLET = ("contanti", "carta", "conto", "investimento", "altro")


class Wallet(Base):
    __tablename__ = "finance_wallets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    tipo: Mapped[str] = mapped_column(String(20), default="altro")
    saldo_iniziale: Mapped[float] = mapped_column(Float, default=0.0)  # saldo di apertura
    note: Mapped[str] = mapped_column(Text, default="")
    ordine: Mapped[int] = mapped_column(Integer, default=0)
    archiviato: Mapped[bool] = mapped_column(Boolean, default=False)
    # accento brand della card (design: strisciolina in alto + chip + barra);
    # vuoto = card neutra con i colori standard del tema
    colore: Mapped[str] = mapped_column(String(20), default="")


class Category(Base):
    __tablename__ = "finance_categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(10), default="")   # "" | uscita | entrata
    archiviato: Mapped[bool] = mapped_column(Boolean, default=False)


class Transaction(Base):
    __tablename__ = "finance_transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo: Mapped[str] = mapped_column(String(15))               # entrata|uscita|trasferimento|giro
    data: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)   # ora locale (app locale)
    importo: Mapped[float] = mapped_column(Float, default=0.0)  # sempre positivo
    wallet_id: Mapped[int] = mapped_column(ForeignKey("finance_wallets.id"))
    # trasferimento: wallet di destinazione — giro: wallet dove entra il rimborso
    wallet_to_id: Mapped[int | None] = mapped_column(ForeignKey("finance_wallets.id"), nullable=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("finance_categories.id"), nullable=True)
    metodo: Mapped[str] = mapped_column(String(60), default="")  # legacy: non più usato (colonna lasciata per non migrare)
    descrizione: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    # --- solo partite di giro (tipo == "giro"): la gamba del rimborso ---
    importo_ricevuto: Mapped[float | None] = mapped_column(Float, nullable=True)   # NULL = aperta
    data_ricevuto: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    controparte: Mapped[str] = mapped_column(String(80), default="")  # da chi (babbo, mamma, ...)

    @property
    def giro_aperta(self) -> bool:
        """Partita di giro ancora in attesa del rimborso."""
        return self.tipo == TIPO_GIRO and self.importo_ricevuto is None

    @property
    def giro_diff(self) -> float | None:
        """Differenza di una partita CHIUSA (ricevuto − speso): l'unica cosa
        che tocca le statistiche. None se aperta o non è un giro."""
        if self.tipo != TIPO_GIRO or self.importo_ricevuto is None:
            return None
        return round((self.importo_ricevuto or 0.0) - (self.importo or 0.0), 2)
