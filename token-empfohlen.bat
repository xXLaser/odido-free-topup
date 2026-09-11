@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo  Empfohlen: odido-bundle-replenisher
echo ========================================
echo.
echo Das ist das aktuellste Windows-Tool (Sept 2026).
echo Es holt den Token selbst und fuellt gratis auf.
echo.
echo 1. Browser oeffnet gleich die Release-Seite
echo 2. Lade: odido-bundle-replenisher-windows.zip
echo 3. Entpacken
echo 4. cmd oeffnen in dem Ordner
echo 5. Ausfuehren:
echo      odido-bundle-replenisher.exe --msisdn +316DEINENUMMER
echo 6. Login-URL oeffnen, einloggen, Ergebnis-URL zurueckkopieren
echo.
echo Details: TOKEN-ALTERNATIVEN.md
echo.
pause
start "" "https://github.com/lodu/odido-bundle-replenisher/releases/latest"
endlocal
