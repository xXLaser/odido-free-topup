@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo  Odido Free Top-up — Ersteinrichtung
echo ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo FEHLER: Python ist nicht installiert oder nicht im PATH.
  echo.
  echo 1. Oeffne https://www.python.org/downloads/
  echo 2. Lade Python 3 herunter und installiere es.
  echo 3. WICHTIG: Haken setzen bei "Add python.exe to PATH"
  echo 4. Danach dieses Fenster schliessen und einrichten.bat erneut starten.
  echo.
  pause
  exit /b 1
)

echo [1/3] Virtuelle Umgebung anlegen...
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  if errorlevel 1 (
    echo FEHLER beim Anlegen der Umgebung.
    pause
    exit /b 1
  )
)

echo [2/3] Pakete installieren...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo FEHLER bei der Installation.
  pause
  exit /b 1
)

echo [3/3] Einstellungsdatei vorbereiten...
if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo.
  echo Die Datei .env wurde angelegt.
  echo Bitte oeffne sie mit Notepad und trage ein:
  echo   - ODIDO_TOKEN=...   (siehe ANLEITUNG.md)
  echo   - ODIDO_MSISDN=...  (Handynummer der SIM, z.B. +31612345678)
  echo.
  notepad ".env"
) else (
  echo .env existiert bereits — wird nicht ueberschrieben.
)

echo.
echo Fertig. Als Naechstes:
echo   1. Token holen (siehe ANLEITUNG.md)
echo   2. In .env eintragen
echo   3. testen.bat starten
echo.
pause
