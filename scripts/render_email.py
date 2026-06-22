#!/usr/bin/env python3
"""Genera l'HTML dell'email da un JSON compatto (template fisso).

Scopo: togliere la generazione dell'HTML dall'output del modello. Il modello
produce solo i dati (analisi); questo script costruisce l'HTML responsive col
design esecutivo navy/grigio. Solo libreria standard.

Uso:
    python scripts/render_email.py --data-file report.json --out out.html

Struttura attesa del JSON (vedi prompts/report.md):
{
  "date": "22 giugno 2026",
  "test_mode": true,
  "diagnostic": {"titoli_cercati": 27, "candidati": 0, "soglia": 60},  # opz.
  "items": [
    {"ticker":"SPCX", "tickers":["SPCX"], "also":"Tocca anche GOOG: ...",
     "tipo_evento":"IPO / NEWS AZIENDALE", "rilevanza":85,
     "titolo":"...", "riassunto":"...",
     "impatto":{"breve":"positivo","medio":"neutro","lungo":"negativo"},
     "confidenza":"media", "tag":["spazio","IPO"],
     "sentiment_analisti":"rating ...",
     "fonti":[{"nome":"CNBC — ...","url":"https://..."}]}
  ]
}
"""
import argparse
import html
import json
import sys

NAVY = "#1a2b4a"
IMPACT = {
    "positivo": ("▲", "#1a7f37", "#e6f4ea"),  # ▲ verde
    "neutro":   ("=",       "#57606a", "#eaeef2"),
    "negativo": ("▼", "#cf222e", "#ffebe9"),  # ▼ rosso
}


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""))


def pill(text, color, bg):
    return (f'<span style="display:inline-block;padding:4px 8px;border-radius:12px;'
            f'margin:2px 4px 2px 0;font-size:13px;white-space:nowrap;'
            f'color:{color};background:{bg};">{esc(text)}</span>')


def impact_block(imp: dict) -> str:
    out = ['<div style="margin:8px 0;">']
    for label, key in (("Breve", "breve"), ("Medio", "medio"), ("Lungo", "lungo")):
        val = (imp or {}).get(key, "neutro")
        arrow, color, bg = IMPACT.get(val, IMPACT["neutro"])
        out.append(pill(f"{label} {arrow} {val}", color, bg))
    return "".join(out) + "</div>"


def card(it: dict) -> str:
    tickers = it.get("tickers") or ([it.get("ticker")] if it.get("ticker") else [])
    tk = " / ".join(esc(t) for t in tickers)
    parts = [f'<div style="width:100%;box-sizing:border-box;background:#ffffff;'
             f'border:1px solid #e1e4e8;border-radius:10px;padding:14px 16px;margin:0 0 14px;">']
    # riga alto: tipo evento + rilevanza
    parts.append(
        f'<div style="font-size:12px;color:{NAVY};font-weight:700;text-transform:uppercase;'
        f'letter-spacing:.4px;">{esc(it.get("tipo_evento","NEWS"))} '
        f'<span style="color:#6a737d;font-weight:600;">· Rilevanza {esc(it.get("rilevanza",""))}/100</span></div>')
    # titolo
    parts.append(f'<div style="font-size:17px;font-weight:700;color:{NAVY};margin:6px 0;">'
                 f'{tk + " — " if tk else ""}{esc(it.get("titolo",""))}</div>')
    # nota "tocca anche"
    if it.get("also"):
        parts.append(f'<div style="background:#fff8e1;border:1px solid #ffe08a;border-radius:8px;'
                     f'padding:8px 10px;margin:6px 0;font-size:13px;color:#7a5d00;">'
                     f'⚠️ {esc(it["also"])}</div>')
    # riassunto
    parts.append(f'<div style="font-size:15px;color:#24292f;line-height:1.5;margin:6px 0;">'
                 f'{esc(it.get("riassunto",""))}</div>')
    # impatto + confidenza
    parts.append(impact_block(it.get("impatto")))
    parts.append('<div>' + pill(f'Confidenza: {it.get("confidenza","n/d")}', "#3a3f45", "#eef1f4") + '</div>')
    # tag
    if it.get("tag"):
        tags = "".join(pill(t, "#555", "#f0f0f0") for t in it["tag"])
        parts.append(f'<div style="margin-top:6px;">{tags}</div>')
    # sentiment analisti
    if it.get("sentiment_analisti"):
        parts.append(f'<div style="font-size:13px;color:#57606a;margin-top:6px;">'
                     f'Analisti: {esc(it["sentiment_analisti"])}</div>')
    # fonti
    fonti = it.get("fonti") or []
    if fonti:
        links = " · ".join(
            f'<a href="{esc(f.get("url",""))}" style="color:#0969da;text-decoration:none;">{esc(f.get("nome","fonte"))}</a>'
            for f in fonti)
        parts.append(f'<div style="font-size:13px;color:#57606a;margin-top:8px;">Fonti: {links}</div>')
    parts.append("</div>")
    return "".join(parts)


def build_html(data: dict) -> str:
    date = esc(data.get("date", ""))
    test = data.get("test_mode")
    title = ("[PROVA] " if test else "") + f"\U0001F4CA Monitor titoli — {date}"
    body = []
    items = data.get("items") or []
    if items:
        body.append(f'<div style="font-size:13px;color:#57606a;margin:0 0 14px;">'
                    f'{len(items)} notizie selezionate, in ordine di rilevanza.</div>')
        body.extend(card(it) for it in items)
    else:
        diag = data.get("diagnostic") or {}
        body.append(
            f'<div style="background:#ffffff;border:1px solid #e1e4e8;border-radius:10px;padding:16px;">'
            f'<div style="font-weight:700;color:{NAVY};font-size:16px;">EMAIL DI PROVA — sistema attivo</div>'
            f'<div style="font-size:14px;color:#24292f;margin-top:8px;line-height:1.5;">'
            f'Nessuna notizia sopra soglia in questa esecuzione. '
            f'Titoli cercati: {esc(diag.get("titoli_cercati","n/d"))} · '
            f'candidati: {esc(diag.get("candidati","0"))} · '
            f'soglia: {esc(diag.get("soglia","n/d"))}.</div></div>')

    disclaimer = (
        "Analisi qualitativa assistita, non una previsione di prezzo e non un consiglio "
        "operativo. Le stime d'impatto hanno il livello di confidenza indicato. "
        "Fonti citate per ogni notizia.")
    return f"""<!DOCTYPE html>
<html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f6f8;">
<div style="width:100%;max-width:600px;margin:0 auto;padding:16px;box-sizing:border-box;
font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#24292f;">
  <div style="background:{NAVY};color:#ffffff;border-radius:10px;padding:16px 18px;margin-bottom:16px;">
    <div style="font-size:19px;font-weight:700;">{esc(title)}</div>
  </div>
  {''.join(body)}
  <div style="font-size:12px;color:#8b949e;line-height:1.5;border-top:1px solid #e1e4e8;
  margin-top:8px;padding-top:12px;">{esc(disclaimer)}</div>
</div></body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Render HTML email da JSON.")
    ap.add_argument("--data-file", required=True)
    ap.add_argument("--out", default="out.html")
    args = ap.parse_args()
    try:
        with open(args.data_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERRORE lettura {args.data_file}: {exc}", file=sys.stderr)
        return 1
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(build_html(data))
    print(f"HTML scritto in {args.out} ({len(data.get('items') or [])} voci)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
