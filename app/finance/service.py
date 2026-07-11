"""Logica delle finanze personali: saldi, movimenti, trasferimenti, giri, sintesi.

Saldo di un wallet = saldo di apertura + entrate - uscite + trasferimenti in arrivo
- trasferimenti in uscita ± le gambe delle partite di giro. Il trasferimento non
cambia il patrimonio totale; la partita di giro lo cambia SOLO della differenza
(ricevuto − speso), che è anche l'unica cosa contata in entrate/uscite del mese.

Tutto DESCRITTIVO: qui l'inserimento e' manuale e strutturato (l'inserimento in
linguaggio naturale passa dall'agente AI, che però compila solo il modulo).
"""
from datetime import datetime

from sqlalchemy import func, select, text

from shared.db import SessionLocal, engine
from finance.models import (Wallet, Category, Transaction,
                            TIPO_ENTRATA, TIPO_USCITA, TIPO_TRASFERIMENTO, TIPO_GIRO)

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
        # partite di giro: la gamba del rimborso sulla stessa riga del movimento
        cols = [r[1] for r in c.execute(text("PRAGMA table_info(finance_transactions)"))]
        for nome, ddl in (("importo_ricevuto", "FLOAT"),
                          ("data_ricevuto", "DATETIME"),
                          ("controparte", "VARCHAR(80) DEFAULT ''")):
            if cols and nome not in cols:
                c.execute(text(f"ALTER TABLE finance_transactions ADD COLUMN {nome} {ddl}"))
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
    """Saldo di ogni wallet, calcolato con poche query aggregate.
    Le partite di giro muovono i saldi con le loro DUE gambe reali: la spesa
    esce da wallet_id, il rimborso (quando c'è) entra in wallet_to_id."""
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
    add(db.query(T.wallet_id, func.sum(T.importo)).filter(T.tipo == TIPO_GIRO).group_by(T.wallet_id), -1)
    add(db.query(T.wallet_to_id, func.sum(T.importo_ricevuto)).filter(
        T.tipo == TIPO_GIRO, T.importo_ricevuto.isnot(None)).group_by(T.wallet_to_id), +1)
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
    # per le partite di giro elimina l'INTERA partita (le due gambe sono una riga)
    with SessionLocal() as db:
        t = db.get(Transaction, tid)
        if t:
            db.delete(t)
            db.commit()


# ------------------------------ partite di giro ------------------------------
def crea_giro(data, importo, wallet_id, controparte="", descrizione="",
              importo_ricevuto=None, data_ricevuto=None, wallet_to_id=None):
    """Registra una partita di giro. Senza la gamba del rimborso
    (importo_ricevuto=None) la partita resta APERTA: il saldo del wallet della
    spesa è già aggiornato ma non conta nulla in entrate/uscite."""
    with SessionLocal() as db:
        db.add(Transaction(
            tipo=TIPO_GIRO, data=data or datetime.now(), importo=abs(importo or 0.0),
            wallet_id=wallet_id, descrizione=(descrizione or "").strip(),
            controparte=(controparte or "").strip(),
            importo_ricevuto=abs(importo_ricevuto) if importo_ricevuto is not None else None,
            data_ricevuto=data_ricevuto if importo_ricevuto is not None else None,
            wallet_to_id=wallet_to_id if importo_ricevuto is not None else None))
        db.commit()


def chiudi_giro(tid, importo_ricevuto, data_ricevuto, wallet_to_id):
    """Chiude una partita aperta registrando il rimborso: da qui in poi la
    differenza (ricevuto − speso) entra nelle statistiche del mese."""
    with SessionLocal() as db:
        t = db.get(Transaction, tid)
        if not t or t.tipo != TIPO_GIRO or t.importo_ricevuto is not None:
            return False
        t.importo_ricevuto = abs(importo_ricevuto or 0.0)
        t.data_ricevuto = data_ricevuto or datetime.now()
        t.wallet_to_id = wallet_to_id
        db.commit()
        return True


def converti_giro_in_uscita(tid):
    """Il rimborso non arriverà mai: la partita aperta diventa una normale
    uscita (stessa data, stesso importo, stesso wallet)."""
    with SessionLocal() as db:
        t = db.get(Transaction, tid)
        if not t or t.tipo != TIPO_GIRO or t.importo_ricevuto is not None:
            return False
        t.tipo = TIPO_USCITA
        t.wallet_to_id = None
        t.data_ricevuto = None
        db.commit()
        return True


def giri_aperti():
    """Partite di giro in attesa di rimborso (le più vecchie prima), con il
    nome del wallet da cui è uscita la spesa: alimentano il riquadro
    'In attesa di rimborso' della pagina Finanze."""
    with SessionLocal() as db:
        wn = {w.id: w.nome for w in db.query(Wallet).all()}
        rows = list(db.execute(
            select(Transaction).where(Transaction.tipo == TIPO_GIRO,
                                      Transaction.importo_ricevuto.is_(None))
            .order_by(Transaction.data, Transaction.id)).scalars().all())
    return [{"t": t, "wallet": wn.get(t.wallet_id, "—")} for t in rows]


def controparti() -> list[str]:
    """I 'da chi' già usati (distinti), per i suggerimenti del modulo."""
    with SessionLocal() as db:
        rows = db.query(Transaction.controparte).filter(
            Transaction.controparte != "").distinct().all()
    return sorted({(r[0] or "").strip() for r in rows if (r[0] or "").strip()},
                  key=str.lower)


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
    dei movimenti reali sulla liquidità. Nessuna stima: solo il registro.
    Una partita di giro produce DUE effetti a due date: la spesa quando esce,
    il rimborso quando (e se) entra."""
    with SessionLocal() as db:
        attivi = {w.id for w in db.query(Wallet).filter(Wallet.archiviato.is_(False)).all()}
        base = sum(w.saldo_iniziale or 0.0 for w in db.query(Wallet).all()
                   if w.id in attivi)
        effetti = []
        for t in db.query(Transaction).all():
            imp = t.importo or 0.0
            if t.tipo == TIPO_ENTRATA and t.wallet_id in attivi:
                effetti.append((t.data, +imp))
            elif t.tipo == TIPO_USCITA and t.wallet_id in attivi:
                effetti.append((t.data, -imp))
            elif t.tipo == TIPO_TRASFERIMENTO:
                if t.wallet_id in attivi:
                    effetti.append((t.data, -imp))
                if t.wallet_to_id in attivi:
                    effetti.append((t.data, +imp))
            elif t.tipo == TIPO_GIRO:
                if t.wallet_id in attivi:
                    effetti.append((t.data, -imp))
                if t.importo_ricevuto is not None and t.wallet_to_id in attivi:
                    effetti.append((t.data_ricevuto or t.data, +(t.importo_ricevuto or 0.0)))

    effetti.sort(key=lambda x: x[0])
    return base, effetti


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
    """Data del primo effetto registrato (None se il registro è vuoto).
    Considera anche i rimborsi delle partite di giro: possono precedere la spesa."""
    with SessionLocal() as db:
        d1 = db.query(func.min(Transaction.data)).scalar()
        d2 = db.query(func.min(Transaction.data_ricevuto)).scalar()
    return min((d for d in (d1, d2) if d), default=None)


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
        giri = db.query(T.importo, T.importo_ricevuto, T.data, T.data_ricevuto).filter(
            T.tipo == TIPO_GIRO, T.importo_ricevuto.isnot(None)).all()
        per_cat = db.query(Category.nome, func.sum(T.importo)).join(
            Category, Category.id == T.category_id).filter(
            T.tipo == TIPO_USCITA, T.data >= start, T.data < end).group_by(
            Category.id).order_by(func.sum(T.importo).desc()).all()
    # Partite di giro CHIUSE: in entrate/uscite conta SOLO la differenza.
    # Ridato di più = entrata alla data del rimborso; ridato di meno = uscita
    # alla data della spesa. Le aperte restano neutre; le gambe intere non
    # compaiono mai qui (muovono solo i saldi dei portafogli).
    for speso, ricevuto, d_spesa, d_rimborso in giri:
        diff = round((ricevuto or 0.0) - (speso or 0.0), 2)
        if diff > 0 and d_rimborso and start <= d_rimborso < end:
            entrate = float(entrate) + diff
        elif diff < 0 and d_spesa and start <= d_spesa < end:
            uscite = float(uscite) - diff
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
