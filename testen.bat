@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Bitte zuerst einrichten.bat ausfuehren.
  pause
  exit /b 1
)

if not exist ".env" (
  echo Datei .env fehlt. Bitte zuerst einrichten.bat ausfuehren.
  pause
  exit /b 1
)

echo Testlauf (nichts wird aufgefuellt, nur pruefen)...
echo.
".venv\Scripts\python.exe" odido_free_topup.py --once --dry-run -v
echo.
pause
endlocal
