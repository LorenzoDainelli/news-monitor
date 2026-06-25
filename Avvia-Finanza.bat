@echo off
chcp 65001 >nul
title Finanza personale - app locale
cd /d "%~dp0app"

REM Primo avvio: crea l'ambiente isolato e installa le librerie (solo la prima volta).
if not exist ".venv\Scripts\python.exe" (
  echo ============================================================
  echo  PRIMO AVVIO: preparo l'ambiente, ci vuole circa un minuto.
  echo  Succede solo questa volta. Attendi senza chiudere...
  echo ============================================================
  python -m venv .venv
  call ".venv\Scripts\activate.bat"
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
) else (
  call ".venv\Scripts\activate.bat"
)

echo.
echo  Avvio dell'app: si aprira' il browser su http://127.0.0.1:8000
echo  Per CHIUDERE l'app, chiudi questa finestra nera.
echo.
python run.py
pause
