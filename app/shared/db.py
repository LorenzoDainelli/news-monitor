"""Motore del database (SQLite via SQLAlchemy).

SQLite = un singolo file sul tuo PC, zero server da installare. SQLAlchemy ci
permette, se un domani serve, di passare a un database 'vero' senza riscrivere
la logica.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from shared.config import DB_URL

# check_same_thread=False: necessario perché il server web usa più thread.
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Classe madre di tutte le tabelle."""
    pass


def get_db():
    """Fornisce una sessione di database a una pagina e la chiude alla fine."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
