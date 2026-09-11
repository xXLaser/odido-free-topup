@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Bitte zuerst einrichten.bat
  pause
  exit /b 1
)

echo Zeige SMS-Speicher und Posteingang...
".venv\Scripts\python.exe" -c "from pathlib import Path; import os,logging; logging.basicConfig(level=logging.DEBUG,format='%(asctime)s [%(levelname)s] %(message)s'); from odido_sms_topup import load_dotenv; load_dotenv(Path('.')/'.env'); from zte_router import ZteRouter; r=ZteRouter(os.environ.get('ZTE_HOST','192.168.0.1'), os.environ['ZTE_PASSWORD'], os.environ.get('ZTE_USER','')); r.login(); print('CAPACITY', r.sms_capacity()); print('INBOX');
[print(m) for m in r.list_sms()]"
echo.
pause
endlocal
