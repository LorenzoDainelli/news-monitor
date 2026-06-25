"""Percorsi e configurazione di base dell'app.

Tutto ciò che è 'dove stanno i file' passa da qui, così se un domani migriamo
l'app su un server (es. Google Cloud Run) basta cambiare questo file.
"""
from pathlib import Path

# .../app  (la cartella dell'app, due livelli sopra questo file: shared/config.py)
APP_DIR = Path(__file__).resolve().parent.parent

# Cartella dei dati LOCALI: database, segreti, cache. Mai su GitHub (vedi .gitignore).
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Database SQLite unico, con tabelle separate per dominio (portfolio_/finance_).
DB_PATH = DATA_DIR / "finanza.db"
DB_URL = f"sqlite:///{DB_PATH}"

# Server locale: solo 127.0.0.1 (il PC stesso), non esposto alla rete. Privacy.
HOST = "127.0.0.1"
PORT = 8000

APP_NAME = "Finanza personale"
