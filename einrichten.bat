@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo  Odido Free Top-up - Ersteinrichtung
echo ========================================
echo.

set "PY="

REM 1) py launcher
where py >nul 2>&1
if not errorlevel 1 (
  for /f "delims=" %%I in ('where py 2^>nul') do (
    if not defined PY set "PY=%%I"
  )
)

REM 2) python on PATH, skip WindowsApps store stub
if not defined PY (
  for /f "delims=" %%I in ('where python 2^>nul') do (
    echo %%I | find /i "\WindowsApps\" >nul
    if errorlevel 1 (
      if not defined PY set "PY=%%I"
    )
  )
)

REM 3) common install locations
if not defined PY if exist "%LocalAppData%\Python\bin\python.exe" set "PY=%LocalAppData%\Python\bin\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python314\python.exe" set "PY=%LocalAppData%\Programs\Python\Python314\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PY=%LocalAppData%\Programs\Python\Python313\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "PY=%LocalAppData%\Programs\Python\Python311\python.exe"
if not defined PY if exist "%ProgramFiles%\Python314\python.exe" set "PY=%ProgramFiles%\Python314\python.exe"
if not defined PY if exist "%ProgramFiles%\Python313\python.exe" set "PY=%ProgramFiles%\Python313\python.exe"
if not defined PY if exist "%ProgramFiles%\Python312\python.exe" set "PY=%ProgramFiles%\Python312\python.exe"

REM 4) Python Install Manager runtimes (pythoncore-*-64)
if not defined PY (
  for /d %%D in ("%LocalAppData%\Python\pythoncore-*-64") do (
    if exist "%%~D\python.exe" if not defined PY set "PY=%%~D\python.exe"
  )
)
if not defined PY (
  for /d %%D in ("%LocalAppData%\Python\pythoncore-*") do (
    if exist "%%~D\python.exe" if not defined PY set "PY=%%~D\python.exe"
  )
)

if not defined PY (
  echo FEHLER: Python wurde nicht gefunden.
  echo.
  echo Auf diesem PC oft vorhanden unter:
  echo   %LocalAppData%\Python\bin
  echo   %LocalAppData%\Python\pythoncore-3.14-64
  echo.
  echo Schnellhilfe:
  echo 1. Windows-Suche: Umgebungsvariablen
  echo 2. Path bearbeiten
  echo 3. Eintrag ...\AppData\Local\Python\bin ganz NACH OBEN
  echo 4. OK, alle Fenster schliessen, einrichten.bat neu starten
  echo.
  echo Oder in cmd:  py install default
  echo.
  pause
  exit /b 1
)

echo Python gefunden: %PY%
"%PY%" --version
if errorlevel 1 (
  echo FEHLER: Python startet nicht.
  pause
  exit /b 1
)
echo.

echo [1/3] Virtuelle Umgebung anlegen...
if not exist ".venv\Scripts\python.exe" (
  "%PY%" -m venv .venv
  if errorlevel 1 (
    echo FEHLER beim Anlegen der Umgebung.
    echo Tipp: In cmd ausfuehren:  py -m venv .venv
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
  echo Bitte in Notepad eintragen:
  echo   ODIDO_TOKEN=...
  echo   ODIDO_MSISDN=+316...
  echo Siehe ANLEITUNG.md
  echo.
  notepad ".env"
) else (
  echo .env existiert bereits - wird nicht ueberschrieben.
)

echo.
echo Fertig. Als Naechstes:
echo   1. Token holen (siehe ANLEITUNG.md)
echo   2. In .env eintragen
echo   3. testen.bat starten
echo.
pause
endlocal
