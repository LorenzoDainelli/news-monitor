"""Filtro privacy: cosa può uscire verso l'AI (Gemini) e cosa no.

Decisione di progetto (filtro PER SEZIONE):
- Finanze: MAI numeri di carta, IBAN o il nome dell'utente.
- Portafoglio investimenti: MAI ISIN, importi, valori o quantità.

Qui ci sono gli strumenti per ripulire un testo libero prima di inviarlo all'AI.
È una rete di sicurezza: l'app già manda solo dati aggregati/scelti dall'utente,
ma se in una frase o in una nota dovesse finire un IBAN o un numero di carta,
viene oscurato. Etica di base (dal CLAUDE.md): mai segnali compra/vendita.
"""
import re

# IBAN: 2 lettere paese + 2 cifre controllo + 10-30 alfanumerici.
_IBAN = re.compile(r"\b[A-Za-z]{2}\d{2}[A-Za-z0-9]{10,30}\b")
# ISIN: 2 lettere + 9 alfanumerici + 1 cifra (12 caratteri).
_ISIN = re.compile(r"\b[A-Za-z]{2}[A-Za-z0-9]{9}\d\b")
# Sequenze lunghe di cifre (eventuali separatori): possibili carte/conti.
_LONGNUM = re.compile(r"\d[\d \-]{11,}\d")


def _redact_numbers(s: str) -> str:
    """Oscura sequenze di 13-19 cifre (carte). Lascia stare importi e date corte."""
    def repl(m):
        digits = re.sub(r"\D", "", m.group())
        return "[numero]" if 13 <= len(digits) <= 19 else m.group()
    return _LONGNUM.sub(repl, s)


def scrub_text(s: str, nome_utente: str = "") -> str:
    """Ripulisce un testo libero da IBAN, ISIN, numeri di carta e nome utente.

    Conservativo: in dubbio oscura. Gli importi normali (poche cifre) restano,
    perché servono al parsing delle spese; non sono un dato sensibile come un
    numero di carta.
    """
    if not s:
        return ""
    s = _IBAN.sub("[IBAN]", s)
    s = _ISIN.sub("[ISIN]", s)
    s = _redact_numbers(s)
    nome = (nome_utente or "").strip()
    if len(nome) >= 3:                     # evita di oscurare nomi troppo corti/comuni
        s = re.sub(re.escape(nome), "[nome]", s, flags=re.I)
    return s.strip()
