"""La memoria dell'agente: cosa ha già detto, e cosa ha capito di te.

Due memorie separate, perché hanno rischi opposti.

**Letture** (memoria episodica). Le ultime cose scritte, con la data e le CHIAVI
dei fatti commentati. Serve a due scopi: poter dire "rispetto a settimana scorsa"
e — più importante — **non ripetere la stessa osservazione ogni volta**. Se ti ho
già detto tre volte che la tecnologia pesa il 37%, la quarta è rumore, e ridurre
il rumore è lo scopo di tutto questo strumento.

**Ricordi** (memoria di profilo). Cose durature capite sull'utente: "il PAC parte
il 16 di ogni mese", "i regali sono stagionali, non un'anomalia". Utilissima e
pericolosa: una conclusione sbagliata si fossilizza, e da lì in poi l'agente
legge tutto attraverso quella lente, con sicurezza crescente e nessuno che lo
corregge.

La contromisura non è tecnica, è di design: **ogni ricordo è una riga che
l'utente apre, legge e cancella**, con la data e il motivo per cui è stato
salvato. Se non fosse ispezionabile, non andrebbe costruita.
"""
from datetime import datetime, timedelta

from sqlalchemy import String, Text, Integer, DateTime, select, delete
from sqlalchemy.orm import Mapped, mapped_column

from shared.db import Base, SessionLocal

TIPO_LETTURA = "lettura"
TIPO_RICORDO = "ricordo"

MAX_LETTURE = 40          # oltre, le più vecchie si potano da sole
MAX_RICORDI = 30          # un profilo più lungo di così non lo leggerebbe nessuno
GIORNI_NON_RIPETERE = 21  # per quanto un'osservazione resta "già detta"


class MemoriaAI(Base):
    """Una riga di memoria. Volutamente una tabella sola e piatta: deve essere
    facile da mostrare in pagina e da cancellare riga per riga."""
    __tablename__ = "ai_memoria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo: Mapped[str] = mapped_column(String(12), index=True)   # lettura | ricordo
    superficie: Mapped[str] = mapped_column(String(20), default="")
    testo: Mapped[str] = mapped_column(Text, default="")
    motivo: Mapped[str] = mapped_column(Text, default="")       # perché l'ho salvato
    chiavi: Mapped[str] = mapped_column(Text, default="")       # fatti commentati, separati da |
    quando: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)


# =========================== letture ===========================
def salva_lettura(superficie: str, testo: str, chiavi=None) -> None:
    """Registra una lettura appena generata e pota le più vecchie."""
    with SessionLocal() as db:
        db.add(MemoriaAI(tipo=TIPO_LETTURA, superficie=superficie,
                         testo=(testo or "").strip(),
                         chiavi="|".join(sorted(chiavi or []))))
        db.commit()
        vecchie = db.execute(
            select(MemoriaAI.id).where(MemoriaAI.tipo == TIPO_LETTURA)
            .order_by(MemoriaAI.quando.desc()).offset(MAX_LETTURE)
        ).scalars().all()
        if vecchie:
            db.execute(delete(MemoriaAI).where(MemoriaAI.id.in_(vecchie)))
            db.commit()


def ultime_letture(superficie: str = "", n: int = 2) -> list:
    with SessionLocal() as db:
        q = select(MemoriaAI).where(MemoriaAI.tipo == TIPO_LETTURA)
        if superficie:
            q = q.where(MemoriaAI.superficie == superficie)
        return list(db.execute(
            q.order_by(MemoriaAI.quando.desc()).limit(n)).scalars().all())


def chiavi_gia_dette(superficie: str = "", giorni: int = GIORNI_NON_RIPETERE) -> set:
    """I fatti già commentati di recente: l'agente deve evitarli, a meno che non
    siano cambiati di molto."""
    limite = datetime.now() - timedelta(days=giorni)
    fuori = set()
    with SessionLocal() as db:
        q = select(MemoriaAI.chiavi).where(
            MemoriaAI.tipo == TIPO_LETTURA, MemoriaAI.quando >= limite)
        if superficie:
            q = q.where(MemoriaAI.superficie == superficie)
        for riga in db.execute(q).scalars().all():
            fuori.update(k for k in (riga or "").split("|") if k)
    return fuori


# =========================== ricordi ===========================
def ricordi() -> list:
    with SessionLocal() as db:
        return list(db.execute(
            select(MemoriaAI).where(MemoriaAI.tipo == TIPO_RICORDO)
            .order_by(MemoriaAI.quando.desc())).scalars().all())


def aggiungi_ricordo(testo: str, motivo: str = "") -> bool:
    """Salva una cosa capita sull'utente. Ritorna False se è vuota, troppo lunga
    o se ne esiste già una uguale: la memoria non deve gonfiarsi di doppioni."""
    testo = " ".join((testo or "").split())[:300]
    if len(testo) < 8:
        return False
    esistenti = ricordi()
    if any(r.testo.lower() == testo.lower() for r in esistenti):
        return False
    with SessionLocal() as db:
        db.add(MemoriaAI(tipo=TIPO_RICORDO, testo=testo,
                         motivo=" ".join((motivo or "").split())[:200]))
        db.commit()
        troppi = db.execute(
            select(MemoriaAI.id).where(MemoriaAI.tipo == TIPO_RICORDO)
            .order_by(MemoriaAI.quando.desc()).offset(MAX_RICORDI)
        ).scalars().all()
        if troppi:
            db.execute(delete(MemoriaAI).where(MemoriaAI.id.in_(troppi)))
            db.commit()
    return True


def dimentica(rid: int) -> bool:
    with SessionLocal() as db:
        r = db.get(MemoriaAI, rid)
        if r is None:
            return False
        db.delete(r)
        db.commit()
        return True


def dimentica_tutto(tipo: str = "") -> int:
    with SessionLocal() as db:
        q = select(MemoriaAI)
        if tipo:
            q = q.where(MemoriaAI.tipo == tipo)
        righe = list(db.execute(q).scalars().all())
        for r in righe:
            db.delete(r)
        db.commit()
        return len(righe)


# =========================== per il prompt ===========================
# L'agente può proporre UNA cosa da ricordare per lettura, su una riga a parte
# che viene tolta dal testo mostrato. Una sola: così la memoria cresce piano e
# resta leggibile.
MARCATORE_RICORDO = "RICORDA:"


def estrai_ricordo(testo: str) -> tuple:
    """Separa l'eventuale riga 'RICORDA: ...' dal testo da mostrare.
    Ritorna (testo_pulito, ricordo_o_vuoto)."""
    righe, ricordo = [], ""
    for r in (testo or "").splitlines():
        if not ricordo and r.strip().upper().startswith(MARCATORE_RICORDO):
            ricordo = r.strip()[len(MARCATORE_RICORDO):].strip()
        else:
            righe.append(r)
    return "\n".join(righe).strip(), ricordo


def come_testo(superficie: str = "") -> str:
    """Il blocco di memoria da mettere nel prompt. Vuoto se non c'è nulla:
    all'inizio l'agente non sa niente di te, ed è giusto così."""
    parti = []
    rs = ricordi()
    if rs:
        parti.append("COSA HAI GIÀ CAPITO DI QUESTO UTENTE (usalo per non "
                     "scambiare un'abitudine per un'anomalia; se un ricordo "
                     "contraddice i fatti di oggi, fidati dei fatti):")
        parti += [f"- {r.testo}" for r in rs]
        parti.append("")

    ultime = ultime_letture(superficie, n=2)
    if ultime:
        parti.append("COSA HAI GIÀ SCRITTO (non ripeterti: se un fatto è lo "
                     "stesso di prima e non è cambiato, lascialo perdere e passa "
                     "ad altro; se invece è cambiato, dì COME è cambiato):")
        for m in ultime:
            parti.append(f"[{m.quando.strftime('%d/%m')}] {m.testo[:400]}")
        parti.append("")

    gia = chiavi_gia_dette(superficie)
    if gia:
        parti.append("Osservazioni già fatte nelle ultime settimane (evitale se "
                     "immutate): " + ", ".join(sorted(gia)))
        parti.append("")
    return "\n".join(parti)
