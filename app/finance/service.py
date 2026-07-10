"""Logica delle finanze personali: saldi, movimenti, trasferimenti, categorie, sintesi.

Saldo di un wallet = saldo di apertura + entrate - uscite + trasferimenti in arrivo
- trasferimenti in uscita. Il trasferimento non cambia il patrimonio totale.

Tutto DESCRITTIVO. L'inserimento in linguaggio naturale e i 'consigli' arrivano con
l'agente AI (Fase 4): qui l'inserimento e' manuale e strutturato.
"""
from datetime import datetime

from sqlalchemy import func, select, text

from shared.db import SessionLocal, engine
from finance.models import (Wallet, Category, Transaction,
                            TIPO_ENTRATA, TIPO_USCITA, TIPO_TRASFERIMENTO)

# Viola ufficiale AIB (Pantone 520 C) — la "strisciolina" brand della card.
AIB_COLORE = "#632874"

# Conti e carte REALI, mai generici (richiesta utente): nome -> (tipo, accento
# brand). I colori di Hype/Revolut/Trade Republic sono copiati 1:1 dal design
# (design_reference/data.js: accent '#12B3A6' / '#5B5BD6' / '#334155').
WALLET_BRAND = {
    "AIB": ("conto", AIB_COLORE),
    "Hype": ("carta", "#12B3A6"),
    "Revolut": ("carta", "#5B5BD6"),
    "Trade Republic": ("carta", "#334155"),
}

# Wallet generici delle prime versioni, da togliere: via se mai usati,
# archiviati (dati preservati) se hanno movimenti o un saldo di apertura.
WALLET_GENERICI = ("Carta di credito", "Conto corrente")

# Portafogli precaricati la prima volta (li puoi rinominare/eliminare).
SEED_WALLETS = [
    ("Contanti", "contanti", ""),
    ("Hype", "carta", WALLET_BRAND["Hype"][1]),
    ("Revolut", "carta", WALLET_BRAND["Revolut"][1]),
    ("Trade Republic", "carta", WALLET_BRAND["Trade Republic"][1]),
    ("AIB", "conto", AIB_COLORE),
    ("PAC investimenti", "investimento", ""),
]


def migra_schema():
    """Colonne aggiunte dopo la prima release: create_all non altera le tabelle
    esistenti, quindi le aggiungiamo qui (idempotente, SQLite)."""
    with engine.connect() as c:
        cols = [r[1] for r in c.execute(text("PRAGMA table_info(finance_wallets)"))]
        if cols and "colore" not in cols:
            c.execute(text("ALTER TABLE finance_wallets ADD COLUMN colore VARCHAR(20) DEFAULT ''"))
            c.commit()


def seed_wallets_if_empty() -> int:
    with SessionLocal() as db:
        if db.query(Wallet).first() is not None:
            return 0
        for i, (nome, tipo, colore) in enumerate(SEED_WALLETS):
            db.add(Wallet(nome=nome, tipo=tipo, saldo_iniziale=0.0, ordine=i,
                          colore=colore))
        db.commit()
        return len(SEED_WALLETS)


def assicura_wallet_brand() -> None:
    """Allinea i portafogli ai conti/carte REALI anche su un DB già popolato:
    crea quelli brand che mancano (AIB, Hype, Revolut, Trade Republic, con il
    loro accento), completa il colore se assente e toglie i generici 'Carta di
    credito' / 'Conto corrente' (eliminati se mai usati, altrimenti archiviati
    così nessun movimento va perso)."""
    with SessionLocal() as db:
        per_nome = {(w.nome or "").strip().lower(): w for w in db.query(Wallet).all()}
        ultimo = db.query(Wallet).order_by(Wallet.ordine.desc()).first()
        ordine = (ultimo.ordine + 1) if ultimo else 0
        for nome, (tipo, colore) in WALLET_BRAND.items():
            w = per_nome.get(nome.lower())
            if w is None:
                db.add(Wallet(nome=nome, tipo=tipo, saldo_iniziale=0.0,
                              ordine=ordine, colore=colore))
                ordine += 1
            elif not (w.colore or "").strip():
                w.colore = colore
        for nome in WALLET_GENERICI:
            w = per_nome.get(nome.lower())
            if w is None or w.archiviato:
                continue
            usato = db.query(Transaction).filter(
                (Transaction.wallet_id == w.id) | (Transaction.wallet_to_id == w.id)).first()
            if usato or (w.saldo_iniziale or 0.0):
                w.archiviato = True
            else:
                db.delete(w)
        db.commit()


# ------------------------------ wallet ------------------------------
def wallets(include_archived: bool = False):
    with SessionLocal() as db:
        q = select(Wallet).order_by(Wallet.ordine, Wallet.id)
        if not include_archived:
            q = q.where(Wallet.archiviato.is_(False))
        return list(db.execute(q).scalars().all())


def _saldi_map(db) -> dict:
    """Saldo di ogni wallet, calcolato con poche query aggregate."""
    saldi = {w.id: w.saldo_iniziale for w in db.query(Wallet).all()}

    def add(query, sign, key="wallet_id"):
        for wid, tot in query:
            if wid in saldi and tot:
                saldi[wid] += sign * tot

    T = Transaction
    add(db.query(T.wallet_id, func.sum(T.importo)).filter(T.tipo == TIPO_ENTRATA).group_by(T.wallet_id), +1)
    add(db.query(T.wallet_id, func.sum(T.importo)).filter(T.tipo == TIPO_USCITA).group_by(T.wallet_id), -1)
    add(db.query(T.wallet_id, func.sum(T.importo)).filter(T.tipo == TIPO_TRASFERIMENTO).group_by(T.wallet_id), -1)
    add(db.query(T.wallet_to_id, func.sum(T.importo)).filter(T.tipo == TIPO_TRASFERIMENTO).group_by(T.wallet_to_id), +1)
    return saldi


def saldi():
    """Lista (wallet, saldo) per i wallet attivi, piu' il patrimonio totale.
    Ordine delle card: saldo decrescente, ma il PAC (tipo 'investimento')
    resta SEMPRE per ultimo, come richiesto."""
    with SessionLocal() as db:
        smap = _saldi_map(db)
        ws = list(db.execute(
            select(Wallet).where(Wallet.archiviato.is_(False)).order_by(Wallet.ordine, Wallet.id)
        ).scalars().all())
    righe = [{"w": w, "saldo": round(smap.get(w.id, 0.0), 2)} for w in ws]
    righe.sort(key=lambda r: (r["w"].tipo == "investimento", -r["saldo"]))
    totale = round(sum(r["saldo"] for r in righe), 2)
    return {"righe": righe, "totale": totale}


# ------------------------------ categorie ------------------------------
def categorie(include_archived: bool = False):
    with SessionLocal() as db:
        q = select(Category).order_by(Category.nome)
        if not include_archived:
            q = q.where(Category.archiviato.is_(False))
        return list(db.execute(q).scalars().all())


def _get_or_create_categoria(db, nome, kind=""):
    nome = (nome or "").strip()
    if not nome:
        return None
    # riusa una categoria esistente con lo stesso nome (niente doppioni)
    ex = db.query(Category).filter(func.lower(Category.nome) == nome.lower(),
                                   Category.archiviato.is_(False)).first()
    if ex:
        return ex.id
    c = Category(nome=nome, kind=kind)
    db.add(c)
    db.flush()
    return c.id


# ------------------------------ movimenti ------------------------------
def crea_movimento(tipo, data, importo, wallet_id, wallet_to_id=None,
                   categoria_nome="", metodo="", descrizione=""):
    with SessionLocal() as db:
        cat_id = None
        if tipo in (TIPO_ENTRATA, TIPO_USCITA):
            cat_id = _get_or_create_categoria(
                db, categoria_nome, "entrata" if tipo == TIPO_ENTRATA else "uscita")
        db.add(Transaction(
            tipo=tipo, data=data or datetime.now(), importo=abs(importo or 0.0),
            wallet_id=wallet_id,
            wallet_to_id=wallet_to_id if tipo == TIPO_TRASFERIMENTO else None,
            category_id=cat_id if tipo != TIPO_TRASFERIMENTO else None,
            metodo=metodo.strip(), descrizione=descrizione.strip()))
        db.commit()


def elimina_movimento(tid):
    with SessionLocal() as db:
        t = db.get(Transaction, tid)
        if t:
            db.delete(t)
            db.commit()


def lista_movimenti(limit=None, mese=None, anno=None):
    """Movimenti ordinati per data e ora decrescenti; senza `limit` li
    restituisce TUTTI (la tabella in pagina mostra l'intero registro)."""
    with SessionLocal() as db:
        wn = {w.id: w.nome for w in db.query(Wallet).all()}
        cn = {c.id: c.nome for c in db.query(Category).all()}
        q = select(Transaction).order_by(Transaction.data.desc(), Transaction.id.desc())
        if anno and mese:
            start, end = _range_mese(anno, mese)
            q = q.where(Transaction.data >= start, Transaction.data < end)
        if limit:
            q = q.limit(limit)
        rows = list(db.execute(q).scalars().all())
    return [{
        "t": t,
        "wallet": wn.get(t.wallet_id, "—"),
        "wallet_to": wn.get(t.wallet_to_id) if t.wallet_to_id else None,
        "categoria": cn.get(t.category_id) if t.category_id else None,
    } for t in rows]


def _range_mese(anno, mese):
    start = datetime(anno, mese, 1)
    end = datetime(anno + (1 if mese == 12 else 0), 1 if mese == 12 else mese + 1, 1)
    return start, end


def _liquidita_walk():
    """Base (saldi di apertura dei wallet attivi) + effetti ordinati per data
    dei movimenti reali sulla liquidità. Nessuna stima: solo il registro."""
    with SessionLocal() as db:
        attivi = {w.id for w in db.query(Wallet).filter(Wallet.archiviato.is_(False)).all()}
        base = sum(w.saldo_iniziale or 0.0 for w in db.query(Wallet).all()
                   if w.id in attivi)
        txs = [(t.data, t.tipo, t.importo or 0.0, t.wallet_id, t.wallet_to_id)
               for t in db.query(Transaction).all()]

    def effetto(tipo, imp, wid, wto):
        e = 0.0
        if tipo == TIPO_ENTRATA and wid in attivi:
            e += imp
        elif tipo == TIPO_USCITA and wid in attivi:
            e -= imp
        elif tipo == TIPO_TRASFERIMENTO:
            if wid in attivi:
                e -= imp
            if wto in attivi:
                e += imp
        return e

    txs.sort(key=lambda x: x[0])
    return base, [(d, effetto(tp, imp, wid, wto)) for d, tp, imp, wid, wto in txs]


def liquidita_alle_date(dates) -> list[float]:
    """Liquidità totale (wallet attivi) a ciascuna delle date indicate (ordinate
    crescenti), ricostruita dai movimenti: usata dal grafico del patrimonio."""
    base, effetti = _liquidita_walk()
    out, cum, i = [], base, 0
    for b in dates:
        while i < len(effetti) and effetti[i][0] < b:
            cum += effetti[i][1]
            i += 1
        out.append(round(cum, 2))
    return out


def prima_data_movimento():
    """Data del primo movimento registrato (None se il registro è vuoto)."""
    with SessionLocal() as db:
        t = db.query(Transaction).order_by(Transaction.data).first()
        return t.data if t else None


def serie_liquidita_12m() -> list[float]:
    """Liquidità totale (wallet attivi) a fine di ognuno degli ultimi 12 mesi,
    RICOSTRUITA dai movimenti reali. Ultimo punto = oggi. Niente stime."""
    now = datetime.now()
    bounds = []
    for k in range(11, 0, -1):
        y, m = _mesi_indietro_ym(now, k - 1)   # inizio del mese successivo al k-esimo
        bounds.append(datetime(y, m, 1))
    bounds.append(now)
    return liquidita_alle_date(bounds)


def _mesi_indietro_ym(now, k):
    y, m = now.year, now.month - k
    while m <= 0:
        m += 12
        y -= 1
    return y, m


def riepilogo_mese(anno, mese):
    start, end = _range_mese(anno, mese)
    T = Transaction
    with SessionLocal() as db:
        entrate = db.query(func.coalesce(func.sum(T.importo), 0.0)).filter(
            T.tipo == TIPO_ENTRATA, T.data >= start, T.data < end).scalar() or 0.0
        uscite = db.query(func.coalesce(func.sum(T.importo), 0.0)).filter(
            T.tipo == TIPO_USCITA, T.data >= start, T.data < end).scalar() or 0.0
        per_cat = db.query(Category.nome, func.sum(T.importo)).join(
            Category, Category.id == T.category_id).filter(
            T.tipo == TIPO_USCITA, T.data >= start, T.data < end).group_by(
            Category.id).order_by(func.sum(T.importo).desc()).all()
    spese = [{"nome": n, "tot": round(float(s), 2)} for n, s in per_cat]
    max_spesa = max((s["tot"] for s in spese), default=0.0)
    for s in spese:
        s["perc"] = round(s["tot"] / max_spesa * 100, 1) if max_spesa else 0
    return {
        "entrate": round(float(entrate), 2),
        "uscite": round(float(uscite), 2),
        "saldo": round(float(entrate) - float(uscite), 2),
        "spese_categoria": spese,
        "anno": anno, "mese": mese,
    }
