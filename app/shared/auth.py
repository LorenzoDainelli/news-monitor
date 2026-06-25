"""Aggancio per il login (predisposizione, NON attivo ora).

Oggi l'app è locale e a utente singolo: nessun login serve. Qui definiamo però fin
da subito il concetto di 'utente corrente' e la dipendenza get_current_user(),
così quando (e se) l'app verrà ospitata online per l'accesso da telefono, basterà
sostituire la logica QUI DENTRO — es. accesso con Google/Apple + 2FA con app
authenticator (TOTP) — senza toccare il resto del codice.

Nota: la 2FA via SMS è stata scartata di proposito perché a pagamento; l'opzione
gratuita equivalente è un'app authenticator.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: str
    nome: str
    is_local: bool = True


# Utente locale predefinito (un solo utente, questo PC).
# In futuro arriverà dalla sessione/login.
LOCAL_USER = User(id="local", nome="Utente locale")


def get_current_user() -> User:
    """Restituisce l'utente corrente.

    SEAM (punto d'aggancio): qui andrà la verifica della sessione/login quando
    l'app sarà ospitata. Per ora ritorna sempre l'utente locale.
    """
    return LOCAL_USER
