"""Avvio comodo: fa partire il server e apre il browser sulla pagina dell'app.

Lo richiama il file Avvia-Finanza.bat (doppio click). Puoi anche eseguirlo a mano:
    python run.py
Per fermare l'app: chiudi la finestra nera, oppure premi CTRL+C.
"""
import threading
import webbrowser

import uvicorn

from shared.config import HOST, PORT


def _apri_browser():
    webbrowser.open(f"http://{HOST}:{PORT}")


if __name__ == "__main__":
    # apre il browser ~1,5s dopo, il tempo che il server sia pronto
    threading.Timer(1.5, _apri_browser).start()
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)
