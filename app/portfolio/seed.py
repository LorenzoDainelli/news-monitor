"""Precarico del portafoglio iniziale (36 asset = 100% + Take-Two a importo fisso).

Fonte delle percentuali: l'allocazione target indicata dall'utente.
Fonte di ticker/ISIN: l'anagrafica gia' verificata in config/portfolio.yaml del
news-monitor (cosi' la lista e' scritta una volta sola).

I dati di DETTAGLIO (prezzi, AUM, TER, holdings...) NON sono qui e NON vanno mai
inventati: arriveranno dalle fonti dati in Fase 2. Qui c'e' solo l'anagrafica.
"""
from shared.db import SessionLocal
from portfolio.models import Position, TIPO_ETF, TIPO_AZIONE

# (nome, tipo, categoria, ticker, isin, pct_target, importo_fisso, note)
SEED = [
    # ===================== ETF (somma 60%) =====================
    ("iShares Core MSCI World UCITS ETF USD (Acc)", TIPO_ETF, "Azionario globale", "IWDA", "IE00B4L5Y983", 20.0, None, ""),
    ("iShares Core S&P 500 UCITS ETF USD (Acc)", TIPO_ETF, "Azionario USA", "CSPX", "IE00B5BMR087", 5.5, None, ""),
    ("iShares Nasdaq 100 UCITS ETF (Acc)", TIPO_ETF, "Tech USA", "CNDX", "IE00B53SZB19", 2.5, None, ""),
    ("Vanguard FTSE All-World High Dividend Yield UCITS ETF (Acc)", TIPO_ETF, "Dividendi globali", "VHYL", "IE00BK5BR626", 6.0, None, ""),
    ("Xtrackers MSCI World Health Care UCITS ETF 1C", TIPO_ETF, "Sanita'", "XDWH", "IE00BM67HK77", 4.0, None, ""),
    ("HANetf Future of Defence UCITS ETF (NATO)", TIPO_ETF, "Difesa", "NATO", "IE000OJ5TQP4", 4.0, None, ""),
    ("VanEck Uranium and Nuclear Technologies UCITS ETF A", TIPO_ETF, "Nucleare & uranio", "NUKL", "IE000M7V94E1", 4.0, None, ""),
    ("Xtrackers MSCI World Materials UCITS ETF 1C", TIPO_ETF, "Materiali", "XDWM", "IE00BM67HS53", 4.0, None, ""),
    ("iShares Global Infrastructure UCITS ETF USD (Acc)", TIPO_ETF, "Infrastrutture", "GIFL", "IE000CK5G8J7", 4.0, None, ""),
    ("Defiance Ukraine Reconstruction UCITS ETF", TIPO_ETF, "Ricostruzione Ucraina", "UKRN", "IE000R8PO127", 2.0, None, ""),
    ("iShares Healthcare Innovation UCITS ETF (Acc)", TIPO_ETF, "Innovazione sanitaria", "HEAL", "IE00BYZK4776", 4.0, None, ""),

    # ===================== AZIONI (somma 40%) =====================
    ("ASML Holding", TIPO_AZIONE, "Semiconduttori", "ASML", "NL0010273215", 3.0, None, ""),
    ("SpaceX", TIPO_AZIONE, "Spazio & difesa", "SPCX", "US84615Q1031", 2.75, None,
     "Neo-quotata su Nasdaq dal 12 giugno 2026: alta volatilita' post-IPO. "
     "Annotare qui la scadenza del lock-up quando nota."),
    ("NVIDIA", TIPO_AZIONE, "Semiconduttori / AI", "NVDA", "US67066G1040", 2.5, None, ""),
    ("Taiwan Semiconductor (TSMC)", TIPO_AZIONE, "Semiconduttori", "TSM", "US8740391003", 2.5, None, ""),
    ("Microsoft", TIPO_AZIONE, "Tech / Cloud", "MSFT", "US5949181045", 2.25, None, ""),
    ("Alphabet (Google)", TIPO_AZIONE, "Tech / Internet", "GOOG", "US02079K3059", 2.25, None, ""),
    ("Broadcom", TIPO_AZIONE, "Semiconduttori", "AVGO", "US11135F1012", 2.0, None, ""),
    ("Intel", TIPO_AZIONE, "Semiconduttori", "INTC", "US4581401001", 2.0, None, ""),
    ("Oracle", TIPO_AZIONE, "Tech / Cloud", "ORCL", "US68389X1054", 1.75, None, ""),
    ("SanDisk (Western Digital)", TIPO_AZIONE, "Hardware / Storage", "WDC", "US9581021055", 1.75, None, ""),
    ("Apple", TIPO_AZIONE, "Tech / Hardware", "AAPL", "US0378331005", 1.5, None, ""),
    ("Samsung Electronics", TIPO_AZIONE, "Tech / Hardware", "SSNLF", "US7960508882", 1.5, None, ""),
    ("Palantir Technologies", TIPO_AZIONE, "Software / AI", "PLTR", "US69608A1088", 1.5, None, ""),
    ("JPMorgan Chase", TIPO_AZIONE, "Finanza / Banche", "JPM", "US46625H1005", 1.25, None, ""),
    ("Eli Lilly", TIPO_AZIONE, "Farmaceutica", "LLY", "US5324571083", 1.25, None, ""),
    ("Amgen", TIPO_AZIONE, "Farmaceutica / Biotech", "AMGN", "US0311621009", 1.25, None, ""),
    ("Amazon", TIPO_AZIONE, "Tech / E-commerce", "AMZN", "US0231351067", 1.0, None, ""),
    ("Meta Platforms", TIPO_AZIONE, "Tech / Social", "META", "US30303M1027", 1.0, None, ""),
    ("Walmart", TIPO_AZIONE, "Retail / Consumi", "WMT", "US9311421039", 1.0, None, ""),
    ("Netflix", TIPO_AZIONE, "Media / Streaming", "NFLX", "US64110L1061", 1.0, None, ""),
    ("Coca-Cola", TIPO_AZIONE, "Beni di consumo", "KO", "US1912161007", 1.0, None, ""),
    ("IBM", TIPO_AZIONE, "Tech / Cloud", "IBM", "US4592001014", 1.0, None, ""),
    ("Shell", TIPO_AZIONE, "Energia", "SHEL", "GB00BP6MXD84", 1.0, None, ""),
    ("Johnson & Johnson", TIPO_AZIONE, "Farmaceutica / Salute", "JNJ", "US4781601046", 1.0, None, ""),
    ("Helios Technologies", TIPO_AZIONE, "Industriale", "HLIO", "US42328H1095", 1.0, None, ""),

    # ============ Asset a importo FISSO (fuori dal 100%) ============
    ("Take-Two Interactive", TIPO_AZIONE, "Gaming / Media", "TTWO", "US87482X1090", 0.0, 1.0,
     "Gestita a importo fisso: 1 €/mese. La % implicita dipende dall'importo PAC."),
]


def seed_if_empty() -> int:
    """Inserisce il portafoglio iniziale solo se la tabella e' vuota.

    Ritorna il numero di posizioni inserite (0 se c'erano gia' dei dati: in quel
    caso non tocca nulla, per non sovrascrivere le tue modifiche).
    """
    with SessionLocal() as db:
        if db.query(Position).first() is not None:
            return 0
        for i, (nome, tipo, cat, ticker, isin, pct, fisso, note) in enumerate(SEED):
            db.add(Position(
                nome=nome, tipo=tipo, categoria=cat, ticker=ticker, isin=isin,
                pct_target=pct, importo_fisso=fisso, note=note, ordine=i,
            ))
        db.commit()
        return len(SEED)
