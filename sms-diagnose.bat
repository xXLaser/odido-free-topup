@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Bitte zuerst einrichten.bat
  pause
  exit /b 1
)

echo Zeige SMS-Speicher und Posteingang...
echo.
".venv\Scripts\python.exe" sms_diagnose.py
echo.
pause
endlocal
