@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Bitte zuerst einrichten.bat
  pause
  exit /b 1
)

echo ========================================
echo  Odido Token in .env speichern
echo ========================================
echo.
echo Token einfuegen (eine Zeile). Oft beginnt er mit: eyJ
echo Wenn du eine loginappresult-URL hast, kannst du die auch einfuegen.
echo.
set /p TOK=Token: 
if "%TOK%"=="" (
  echo Abbruch.
  pause
  exit /b 1
)

echo.
set /p MSISDN=Handynummer z.B. +31612345678: 
if "%MSISDN%"=="" (
  echo Abbruch.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" token_speichern.py "%TOK%" "%MSISDN%"
if errorlevel 1 (
  echo Fehler.
  pause
  exit /b 1
)

echo.
echo Fertig. Starte jetzt: testen.bat
echo.
pause
endlocal
