"""Preferenze dell'interfaccia: tema (chiaro/scuro) e lingua.

Salvate nel database locale (tabella delle impostazioni). Per ora valgono per
tutta l'app; quando ci sarà il login diventeranno per-utente (vedi auth.py).
"""
from shared.settings_store import get_setting, set_setting, get_many
from shared.i18n import LANG_CODES, DEFAULT_LANG

VALID_THEMES = ("light", "dark")
# Intensità delle animazioni dei portafogli: piene (esuberanti), leggere, spente.
VALID_ANIM = ("piene", "leggere", "spente")
DEFAULT_ANIM = "piene"


def get_anim() -> str:
    v = get_setting("ui_anim", DEFAULT_ANIM)
    return v if v in VALID_ANIM else DEFAULT_ANIM


def set_anim(value: str) -> None:
    if value in VALID_ANIM:
        set_setting("ui_anim", value)


def get_theme() -> str:
    v = get_setting("ui_theme", "light")
    return v if v in VALID_THEMES else "light"


def set_theme(value: str) -> None:
    if value in VALID_THEMES:
        set_setting("ui_theme", value)


def get_lang() -> str:
    v = get_setting("ui_lang", DEFAULT_LANG)
    return v if v in LANG_CODES else DEFAULT_LANG


def get_ui() -> dict:
    """Tema+lingua+animazioni in UNA query (chiamata a ogni pagina)."""
    vals = get_many(("ui_theme", "ui_lang", "ui_anim"))
    theme = vals.get("ui_theme", "light")
    lang = vals.get("ui_lang", DEFAULT_LANG)
    anim = vals.get("ui_anim", DEFAULT_ANIM)
    return {
        "theme": theme if theme in VALID_THEMES else "light",
        "lang": lang if lang in LANG_CODES else DEFAULT_LANG,
        "anim": anim if anim in VALID_ANIM else DEFAULT_ANIM,
    }


def set_lang(value: str) -> None:
    if value in LANG_CODES:
        set_setting("ui_lang", value)
