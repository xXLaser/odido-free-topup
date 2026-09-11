@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo  Odido Token holen
echo ========================================
echo.
echo WICHTIG:
echo  1. Am Ende erscheint ein langer Token-Text.
echo  2. SOFORT markieren (Maus) und kopieren (Strg+C).
echo  3. In .env bei ODIDO_TOKEN= einfuegen.
echo  4. Dieses Fenster bleibt offen - nichts geht verloren.
echo.

set "AUTH="
if exist "%~dp0Odido.Authenticator.exe" set "AUTH=%~dp0Odido.Authenticator.exe"
if not defined AUTH if exist "%~dp0Odido-Authenticator\Odido.Authenticator.exe" set "AUTH=%~dp0Odido-Authenticator\Odido.Authenticator.exe"
if not defined AUTH if exist "%USERPROFILE%\Downloads\Odido.Authenticator.exe" set "AUTH=%USERPROFILE%\Downloads\Odido.Authenticator.exe"
if not defined AUTH if exist "%USERPROFILE%\Downloads\Odido-Authenticator\Odido.Authenticator.exe" set "AUTH=%USERPROFILE%\Downloads\Odido-Authenticator\Odido.Authenticator.exe"

if not defined AUTH (
  echo Odido.Authenticator.exe nicht gefunden.
  echo.
  echo 1. Lade herunter:
  echo    https://github.com/GuusBackup/Odido.Authenticator/releases/latest
  echo 2. ZIP entpacken
  echo 3. Odido.Authenticator.exe in DIESEN Ordner kopieren:
  echo    %~dp0
  echo 4. token-holen.bat erneut starten
  echo.
  pause
  exit /b 1
)

echo Starte: %AUTH%
echo.
echo Ablauf im Authenticator:
echo  - URL oeffnen, bei Odido einloggen
echo  - Ergebnis-URL zurueckkopieren, Enter
echo  - Wenn nach Y gefragt: Y tippen, Enter
echo  - Token SOFORT kopieren (langer Text)
echo.
pause

"%AUTH%"

echo.
echo ========================================
echo Fenster bleibt offen.
echo Token oben kopieren und in .env einfuegen:
echo   ODIDO_TOKEN=hier_den_ganzen_token
echo Dann Notepad speichern und testen.bat starten.
echo ========================================
echo.
pause
endlocal
