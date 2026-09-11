@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Bitte zuerst einrichten.bat ausfuehren.
  pause
  exit /b 1
)

echo Sende JETZT gratis EXTRA an 1280 ueber den ZTE-Router...
echo.
".venv\Scripts\python.exe" odido_sms_topup.py --once-extra -v
echo.
pause
endlocal
