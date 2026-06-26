"""Logica delle finanze personali: saldi, movimenti, trasferimenti, categorie, sintesi.

Saldo di un wallet = saldo di apertura + entrate - uscite + trasferimenti in arrivo
- trasferimenti in uscita. Il trasferimento non cambia il patrimonio totale.

Tutto DESCRITTIVO. L'inserimento in linguaggio naturale e i 'consigli' arrivano con
l'agente AI (Fase 4): qui l'inserimento e' manuale e strutturato.
"""
from datetime import datetime

from sqlalchemy import func, select

from shared.db import SessionLocal
from finance.models import (Wallet, Category, Transaction,
                            TIPO_ENTRATA, TIPO_USCITA, TIPO_TRASFERIMENTO)

# Portafogli tipici precaricati la prima volta (li puoi rinominare/eliminare).
SEED_WALLETS = [
    ("Contanti", "contanti"),
    ("Carta di credito", "carta"),
    ("Conto corrente", "conto"),
    ("PAC investimenti", "investimento"),
]


def seed_wallets_if_empty() -> int:
    with SessionLocal() as db:
        if db.query(Wallet).first() is not None:
            return 0
        for i, (nome, tipo) in enumerate(SEED_WALLETS):
            db.add(Wallet(nome=nome, tipo=tipo, saldo_iniziale=0.0, ordine=i))
        db.commit()
        return len(SEED_WALLETS)


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
    """Lista (wallet, saldo) per i wallet attivi, piu' il patrimonio totale."""
    with SessionLocal() as db:
        smap = _saldi_map(db)
        ws = list(db.execute(
            select(Wallet).where(Wallet.archiviato.is_(False)).order_by(Wallet.ordine, Wallet.id)
        ).scalars().all())
    righe = [{"w": w, "saldo": round(smap.get(w.id, 0.0), 2)} for w in ws]
    totale = round(sum(r["saldo"] for r in righe), 2)
    return {"righe": righe, "totale": totale}


def crea_wallet(nome, tipo, saldo_iniziale, note=""):
    with SessionLocal() as db:
        ultimo = db.query(Wallet).order_by(Wallet.ordine.desc()).first()
        db.add(Wallet(nome=nome.strip(), tipo=tipo, saldo_iniziale=saldo_iniziale or 0.0,
                      note=note.strip(), ordine=(ultimo.ordine + 1) if ultimo else 0))
        db.commit()


def aggiorna_wallet(wid, nome, tipo, saldo_iniziale, note=""):
    with SessionLocal() as db:
        w = db.get(Wallet, wid)
        if w:
            w.nome, w.tipo, w.saldo_iniziale, w.note = nome.strip(), tipo, saldo_iniziale or 0.0, note.strip()
            db.commit()


def elimina_wallet(wid):
    """Elimina un wallet solo se non ha movimenti; altrimenti lo archivia."""
    with SessionLocal() as db:
        usato = db.query(Transaction).filter(
            (Transaction.wallet_id == wid) | (Transaction.wallet_to_id == wid)).first()
        w = db.get(Wallet, wid)
        if not w:
            return
        if usato:
            w.archiviato = True
        else:
            db.delete(w)
        db.commit()


def get_wallet(wid):
    with SessionLocal() as db:
        return db.get(Wallet, wid)


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


def rinomina_categoria(cid, nuovo_nome):
    with SessionLocal() as db:
        c = db.get(Category, cid)
        if c:
            c.nome = nuovo_nome.strip()
            db.commit()


def unisci_categorie(da_id, a_id):
    """Sposta i movimenti dalla categoria 'da' alla 'a' e archivia 'da'."""
    if da_id == a_id:
        return
    with SessionLocal() as db:
        db.query(Transaction).filter(Transaction.category_id == da_id).update(
            {Transaction.category_id: a_id})
        c = db.get(Category, da_id)
        if c:
            c.archiviato = True
        db.commit()


def elimina_categoria(cid):
    with SessionLocal() as db:
        db.query(Transaction).filter(Transaction.category_id == cid).update(
            {Transaction.category_id: None})
        c = db.get(Category, cid)
        if c:
            db.delete(c)
        db.commit()


# ------------------------------ movimenti ------------------------------
def crea_movimento(tipo, data, importo, wallet_id, wallet_to_id=None,
                   categoria_nome="", metodo="", descrizione=""):
    with SessionLocal() as db:
        cat_id = None
        if tipo in (TIPO_ENTRATA, TIPO_USCITA):
            cat_id = _get_or_create_categoria(
                db, categoria_nome, "entrata" if tipo == TIPO_ENTRATA else "uscita")
        db.add(Transaction(
            tipo=tipo, data=data or datetime.utcnow(), importo=abs(importo or 0.0),
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


def lista_movimenti(limit=100, mese=None, anno=None):
    with SessionLocal() as db:
        wn = {w.id: w.nome for w in db.query(Wallet).all()}
        cn = {c.id: c.nome for c in db.query(Category).all()}
        q = select(Transaction).order_by(Transaction.data.desc(), Transaction.id.desc())
        if anno and mese:
            start, end = _range_mese(anno, mese)
            q = q.where(Transaction.data >= start, Transaction.data < end)
        rows = list(db.execute(q.limit(limit)).scalars().all())
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
