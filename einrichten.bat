@echo off
chcp 65001 >nul
cd /d "%~dp0"
setlocal EnableExtensions

echo ========================================
echo  Odido Free Top-up — Ersteinrichtung
echo ========================================
echo.

set "PY="

REM 1) py-Launcher (oft nach python.org-Installation vorhanden)
where py >nul 2>&1
if not errorlevel 1 (
  for /f "delims=" %%I in ('where py 2^>nul') do (
    if not defined PY set "PY=%%I"
  )
)

REM 2) python im PATH — aber Microsoft-Store-Attrappe ueberspringen
if not defined PY (
  for /f "delims=" %%I in ('where python 2^>nul') do (
    echo %%I | find /i "\WindowsApps\" >nul
    if errorlevel 1 (
      if not defined PY set "PY=%%I"
    )
  )
)

REM 3) Typische Installationsorte (auch ohne PATH)
if not defined PY if exist "%LocalAppData%\Python\bin\python.exe" set "PY=%LocalAppData%\Python\bin\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PY=%LocalAppData%\Programs\Python\Python313\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "PY=%LocalAppData%\Programs\Python\Python311\python.exe"
if not defined PY if exist "%ProgramFiles%\Python313\python.exe" set "PY=%ProgramFiles%\Python313\python.exe"
if not defined PY if exist "%ProgramFiles%\Python312\python.exe" set "PY=%ProgramFiles%\Python312\python.exe"

if not defined PY (
  echo FEHLER: Python wurde nicht gefunden.
  echo.
  echo Auf diesem PC oft schon vorhanden unter:
  echo   %LocalAppData%\Python\bin
  echo.
  echo Schnellhilfe PATH (Freund-PC):
  echo 1. Windows-Suche: "Umgebungsvariablen"
  echo 2. "Umgebungsvariablen bearbeiten" oeffnen
  echo 3. Bei Benutzervariablen "Path" markieren -^> Bearbeiten
  echo 4. Eintrag "...\AppData\Local\Python\bin" ganz NACH OBEN schieben
  echo    (ueber WindowsApps!)
  echo 5. OK - OK - ALLE Fenster schliessen
  echo 6. einrichten.bat NOCHMAL starten (neues Fenster)
  echo.
  echo Oder neu installieren: https://www.python.org/downloads/
  echo (neuer Install Manager: KEIN PATH-Haken — das ist normal)
  echo Falls gefragt "PATH hinzufuegen?" -^> Ja
  echo Oder in cmd:   py install default
  echo.
  pause
  exit /b 1
)

echo Python gefunden: %PY%
"%PY%" --version
if errorlevel 1 (
  echo FEHLER: Python startet nicht. Bitte neu installieren von python.org
  pause
  exit /b 1
)
echo.

echo [1/3] Virtuelle Umgebung anlegen...
if not exist ".venv\Scripts\python.exe" (
  "%PY%" -m venv .venv
  if errorlevel 1 (
    echo FEHLER beim Anlegen der Umgebung.
    echo Tipp: Bei manchen Python-Installationen fehlt "venv".
    echo Dann python.org-Installer nutzen und "Install Now" waehlen.
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
endlocal
