@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Bitte zuerst einrichten.bat ausfuehren.
  pause
  exit /b 1
)

echo Test: einmal EXTRA an 1280 senden (DRY-RUN = kein SMS)...
echo.
".venv\Scripts\python.exe" odido_sms_topup.py --once-extra --dry-run -v
echo.
echo Wenn Login OK war, echtes Senden mit:
echo   testen-sms.bat ohne dry-run  ODER
echo   ".venv\Scripts\python.exe" odido_sms_topup.py --once-extra
echo.
pause
endlocal
