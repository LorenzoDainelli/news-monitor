"""Tabelle delle finanze personali: portafogli (conti/wallet), categorie, movimenti.

Tre tipi di movimento:
- entrata        -> aumenta il saldo del wallet
- uscita         -> diminuisce il saldo del wallet
- trasferimento  -> sposta denaro da un wallet all'altro (NON cambia il patrimonio
                    totale, cambia solo i due saldi)

Prefisso tabelle 'finance_' per non interferire col modulo portafoglio.
"""
from datetime import datetime

from sqlalchemy import String, Float, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from shared.db import Base

TIPO_ENTRATA = "entrata"
TIPO_USCITA = "uscita"
TIPO_TRASFERIMENTO = "trasferimento"
TIPI_MOVIMENTO = (TIPO_ENTRATA, TIPO_USCITA, TIPO_TRASFERIMENTO)

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


class Category(Base):
    __tablename__ = "finance_categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(10), default="")   # "" | uscita | entrata
    archiviato: Mapped[bool] = mapped_column(Boolean, default=False)


class Transaction(Base):
    __tablename__ = "finance_transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo: Mapped[str] = mapped_column(String(15))               # entrata|uscita|trasferimento
    data: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    importo: Mapped[float] = mapped_column(Float, default=0.0)  # sempre positivo
    wallet_id: Mapped[int] = mapped_column(ForeignKey("finance_wallets.id"))
    wallet_to_id: Mapped[int | None] = mapped_column(ForeignKey("finance_wallets.id"), nullable=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("finance_categories.id"), nullable=True)
    metodo: Mapped[str] = mapped_column(String(60), default="")
    descrizione: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
