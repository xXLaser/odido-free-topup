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

echo ========================================
echo  Odido SMS Top-up (ZTE-Router)
echo  Nur GRATIS: EXTRA an 1280
echo  Fenster offen lassen. Beenden: Strg+C
echo ========================================
echo.

".venv\Scripts\python.exe" odido_sms_topup.py
pause
endlocal
