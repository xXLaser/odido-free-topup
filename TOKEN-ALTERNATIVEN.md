# Token-Weg: Alternativen (Stand Sept. 2026)

Die SMS-Variante fällt aus, wenn der ZTE keine SMS senden kann.  
Dann bleibt die **Odido Customer API** (`A0DAY01` = gratis 2 GB). Dafür brauchst du einen **Bearer-Token**.

## Was oft schiefgeht

| Problem | Erklärung |
| --- | --- |
| Authenticator-Fenster zu | Nach `Y` schließt sich die EXE — Token weg |
| Falscher Token | Die **komplette Browser-URL** ist nicht der Bearer-Token; oder nur der Refresh-Token wurde kopiert |
| Token abgelaufen | Bearer-Tokens laufen ab → neu holen |
| 2FA / Login-Flow geändert | Alte Tools (2023) können haken |

---

## Alternative A — empfohlen: odido-bundle-replenisher (Windows)

Aktuell gepflegt (Release **v1.2.0**, 8.9.2026). Enthält Login **und** automatisches Auffüllen.

1. Download: https://github.com/lodu/odido-bundle-replenisher/releases/latest  
2. Unter Assets: **`odido-bundle-replenisher-windows.zip`**  
3. Entpacken  
4. In **cmd** (nicht nur Doppelklick):

```text
cd Pfad\zum\entpackten\Ordner
odido-bundle-replenisher.exe --msisdn +316xxxxxxxx
```

(ohne Token startet der Login-Assistent)

5. Angezeigte URL im Browser öffnen → bei Odido einloggen  
6. Die **Ergebnis-URL** aus der Adresszeile kopieren (beginnt oft mit `loginappresult?token=`)  
7. In die cmd zurück: URL einfügen → Enter  
8. Das Programm speichert/zeigt Tokens — danach läuft die Automatik

**Vorteil:** Kein separates Authenticator-Tool, Fenster bleibt in cmd offen, Code aktuell.

Du kannst dieses Programm **statt** unserem Python-Script nutzen — es macht denselben Job (gratis Aanvuller).

---

## Alternative B — Guus Odido.Authenticator + unser Script

1. https://github.com/GuusBackup/Odido.Authenticator/releases/latest  
2. `Odido.Authenticator.exe` in den Ordner `odido-free-topup` legen  
3. **`token-holen.bat`** starten (hält das Fenster offen)  
4. URL öffnen → einloggen → Ergebnis-URL einfügen → bei `Y` den **langen Authentication Token** kopieren  
5. In `.env`: `ODIDO_TOKEN=...` und `ODIDO_MSISDN=+316...`  
6. `testen.bat` → `starten.bat`

**Tipp:** Token mit Notepad in `.env` speichern, **bevor** du das Fenster schließt.  
Oder: `token-speichern.bat` nutzen (fragt den Token ab und schreibt `.env`).

---

## Alternative C — Benutzername + Passwort (TmobileRefresh)

https://github.com/Skamba/TmobileRefresh  

- Loggt mit Odido-Login/Passwort ein und fordert `A0DAY01` an  
- Projekt ist **archiviert** (letzter Push Feb. 2026) — kann mit neuer 2FA/Login-Änderung brechen  
- Nur wenn A/B nicht klappen und du .NET nutzen willst  

---

## Alternative D — ohne Automatisierung (zuverlässig)

1. SIM kurz ins **Handy**  
2. Odido-App: gratis 2‑GB-Aanvuller tippen **oder** SMS `EXTRA` an `1280`  
3. SIM zurück in den ZTE  

Für gelegentliche große Downloads oft praktischer als Token-Kampf.

---

## Alternative E — iPhone Cache (nur Apple)

https://github.com/ink-splatters/odido-aap  

Token aus der Odido-iOS-App / Backup — nur relevant mit iPhone und etwas Technik.

---

## Welchen Token braucht unser Python-Script?

In `.env`:

```text
ODIDO_TOKEN=eyJhbGciOi...ganz_langer_bearer...
ODIDO_MSISDN=+31612345678
```

- Das ist ein **Bearer-Access-Token** (oft beginnt mit `eyJ` wenn JWT)  
- **Nicht** die ganze `https://www.odido.nl/loginappresult?token=...` URL (außer ein Tool sagt explizit, die URL einzufügen — dann wandelt *das Tool* sie um)  
- Nach dem Eintragen: `testen.bat`  
  - Erfolg: Rest-MB werden angezeigt  
  - 401/403: Token ungültig/abgelaufen → neu holen  

---

## Empfehlung für euch (ZTE ohne SMS)

1. **Zuerst Alternative A** (`odido-bundle-replenisher` Windows) — alles-in-einem  
2. Wenn das Login dort klappt: fertig (Automatik läuft)  
3. Wenn du bei unserem Script bleiben willst: Token aus A in `.env` als `ODIDO_TOKEN` übernehmen  
4. Notfall: Alternative D (Handy)
