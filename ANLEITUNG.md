# Odido Fair Use — Guthaben automatisch gratis nachladen

**Geprüft am: 11. September 2026**

Diese Anleitung ist für Leute gedacht, die **keinen IT-Hintergrund** haben.  
Du brauchst einen normalen Windows-PC und deine Odido-SIM (z. B. im ZTE-Router).

---

## Was macht das Programm?

Bei Odido **Unlimited** bekommst du jeden Tag **20 GB** schnelles Internet in den Niederlanden.  
Sind die fast leer, darfst du **so oft du willst kostenlos 2 GB nachladen** („Aanvuller“).

Es gibt **zwei Wege** (beides nur gratis):

| Variante | Wie | Wann nutzen |
| --- | --- | --- |
| **B — SMS über ZTE-Router** | PC schickt per Router-SMS `EXTRA` an **1280** | **Empfohlen**, wenn der App-Token nicht klappt |
| A — Odido-API mit Token | Wie die App, BuyingCode `A0DAY01` | Wenn Token-Holen funktioniert |

Laut Odido-Support geht der gratis 2‑GB-Aanvuller u. a. per SMS: **EXTRA → 1280**.

| Was | Antwort |
| --- | --- |
| Kostet das Nachladen etwas? | **Nein** (nur Unlimited-Fair-Use / EXTRA an 1280). |
| Muss ich am Router etwas umbauen? | **Nein.** Der PC spricht die Router-Weboberfläche an. |
| Wo läuft das Programm? | Auf dem **PC** im WLAN/LAN des Routers. |
| Wann brauche ich es? | Wenn du an einem Tag **mehr als 20 GB** brauchst. |

---

## Ist das noch aktuell?

Stand September 2026:

- Odido beschreibt Fair Use weiter so: **20 GB/Tag**, danach **gratis 2 GB** so oft wie nötig.  
  Quelle: [Odido FAQ](https://www.odido.nl/service/veelgestelde-vragen/waarom-krijg-ik-20-gb-per-dag-ik-heb-toch-unlimited/000453219)
- Der technische Code dafür (`A0DAY01`) ist weiterhin der Standard in aktuellen Community-Tools (letztes Update u. a. **8.9.2026**).
- Es gibt **keine offizielle Odido-Automation**. Das hier nutzt die gleiche Schnittstelle wie die App — **auf eigene Verantwortung**.

**Wichtig:** Das gilt für **Unlimited** mit Fair Use.  
Nicht für Verträge ohne diese gratis Aanvullers — dort könnte Nachladen **Geld kosten**. Dann dieses Programm **nicht** nutzen.

---

## Was du brauchst

1. Windows-PC im WLAN/LAN des ZTE-Routers
2. Odido **Unlimited** (Fair Use mit gratis Aanvullers)
3. **Python** — Installation siehe Schritt 1
4. Für **SMS-Variante:** Router-Passwort (wie beim Login im Browser, oft `192.168.0.1`)
5. Für **Token-Variante:** Odido-Login + Authenticator (Schritt 3 weiter unten)

---

## Schritt für Schritt

### Schritt 1 — Python installieren (einmalig)

Auf python.org kommt oft der neue **Python Install Manager** (manchmal „Download Manager“).  
Dort gibt es **keinen** Haken „Add python.exe to PATH“ — das ist normal.

So machst du es:

1. Öffne https://www.python.org/downloads/
2. Lade den Installer / Manager herunter und starte ihn
3. Wenn er fragt, ob etwas zu **PATH** hinzugefügt werden soll → **Ja / Yes**
4. Python installieren lassen (oft reicht „Install“ / neueste Version)
5. Alle Fenster schließen

Wenn danach etwas von „configure“ / Einstellungen kommt und nach PATH fragt: wieder **Ja**.

#### Alternativ im Terminal (falls GUI unklar ist)

Windows-Taste → `cmd` → Enter, dann eingeben:

```text
py install default
```

Wenn gefragt wird wegen PATH / konfigurieren:

```text
py install --configure
```

und dort **Ja** wählen, wenn PATH angeboten wird.

#### Python ist da, aber `einrichten.bat` findet es nicht?

Auf manchen PCs steht Python schon unter  
`C:\Users\...\AppData\Local\Python\bin` — aber **WindowsApps** steht darüber im PATH und blockiert es.

Im Fenster **„Umgebungsvariable bearbeiten“** (Path):

1. Den Eintrag `...\AppData\Local\Python\bin` markieren  
2. Mehrfach **„Nach oben“** klicken, bis er **ganz oben** steht (über WindowsApps)  
3. **OK** → **OK**  
4. Alle CMD-/Einrichtungsfenster **schließen**  
5. **`einrichten.bat` erneut** per Doppelklick starten  

Die aktuelle `einrichten.bat` (ab Release **v1.0.1**) sucht Python auch direkt in diesem Ordner — oft reicht schon ein erneuter Start mit der neuen Version.

---

### Schritt 2 — Dieses Programm einrichten (einmalig)

1. Ordner mit dem Programm öffnen  
   (z. B. Download von GitHub entpacken, oder der Ordner `odido-free-topup` auf dem PC)
2. Doppelklick auf **`einrichten.bat`**
3. Warte, bis „Fertig“ erscheint
4. Es öffnet sich die Datei **`.env`** im Editor (Notepad)

In der Datei siehst du ungefähr:

```text
ODIDO_TOKEN=hier_dein_token_einfuegen
ODIDO_MSISDN=+31612345678
```

- Bei **`ODIDO_MSISDN=`** trägst du die echte Nummer der SIM ein, z. B. `+31612345678`  
  (ohne Leerzeichen)
- Bei **`ODIDO_TOKEN=`** kommt später der Zugangscode rein (nächster Schritt)

Speichern und Notepad schließen.

---

### Schritt 2b — SMS-Variante über den ZTE-Router (ohne Token)

Das ist der Weg, wenn Schritt 3 (Token) nicht klappt.

1. Im Browser die Router-Seite öffnen (meist `http://192.168.0.1` oder `http://192.168.1.1`)  
   und prüfen, dass Login mit Benutzer/Passwort funktioniert.
2. In der Datei **`.env`** eintragen (Beispiel):

```text
ZTE_HOST=192.168.0.1
ZTE_USER=
ZTE_PASSWORD=WebsitePasswortVomAufkleber
ZTE_INTERVAL=120
ZTE_PERIODIC_EXTRA_MINUTES=0
```

**MC888 / MC888 Pro — wichtig:**

1. Passwort = **Website-/Admin-Passwort** vom Aufkleber am Router  
   (nicht das WLAN-Passwort!)
2. In `.env` **ohne** Anführungszeichen, z. B. `ZTE_PASSWORD=Ab12cd34`
3. `ZTE_USER=` leer lassen
4. Browser-Tab mit der Router-Seite **schließen**, bevor du das Script startest
5. Dann `sms-extra-jetzt.bat`

Wenn die Meldung `result=1` kommt: Passwort ist falsch → Aufkleber / in der Web-UI gesetztes Admin-Passwort prüfen.

3. Doppelklick **`testen-sms.bat`** (nur Login-Test, sendet noch keine SMS)
4. Wenn das OK aussieht: **`sms-extra-jetzt.bat`** — sendet **einmal** `EXTRA` an **1280** (gratis Aanvuller)
5. Dauerhaft: **`starten-sms.bat`**  
   - Liest den SMS-Posteingang des Routers  
   - Wenn Odido eine Hinweis-SMS schickt → sendet automatisch `EXTRA` an 1280  
   - Sendet **keine** bezahlten Pakete (Nummer/Text sind fest verdrahtet)

**Tipp bei großen Downloads:** In `.env` z. B. `ZTE_PERIODIC_EXTRA_MINUTES=45` setzen.  
Dann wird alle 45 Minuten vorsorglich `EXTRA` geschickt (Odido akzeptiert das oft nur, wenn wenig Rest übrig ist).

**Wichtig:** PC muss im Netz des ZTE-Routers sein. Router-Modell idealerweise ZTE MC801 / MC888 / ähnlich.

---

### Schritt 3 — Zugangscode (Token) holen

Das Programm braucht einen **Zugangscode**, damit Odido weiß: „Das bist du.“  
Das ist **kein Passwort zum Weitergeben**. Behandle es wie ein Passwort.

**Problem:** Wenn man den Authenticator per Doppelklick startet, schließt sich das Fenster oft  
sofort nach dem Token — dann kannst du ihn nicht mehr ablesen.  
Deshalb: **`token-holen.bat`** nutzen (Fenster bleibt offen).

1. Lade herunter: https://github.com/GuusBackup/Odido.Authenticator/releases/latest  
   → unter **Assets** die Datei **`Odido-Authenticator.zip`**
2. ZIP entpacken
3. Die Datei **`Odido.Authenticator.exe`** in den Ordner `odido-free-topup` **kopieren**  
   (derselbe Ordner wie `einrichten.bat`)
4. Doppelklick auf **`token-holen.bat`**
5. Im Authenticator erscheint eine **Internetadresse** → im Browser öffnen
6. Bei Odido **einloggen**
7. Nach dem Login: die **komplette Adresse** aus der Browser-Zeile kopieren  
   (beginnt mit `https://www.odido.nl/loginappresult?token=...`)
8. Zurück ins schwarze Fenster: Adresse **einfügen** → **Enter**
9. Wenn nach **Y** gefragt wird: **`Y`** tippen → **Enter**
10. Es erscheint ein **langer Token** (viele Zeichen)  
    → **sofort markieren und kopieren** (Strg+C)  
    → das Fenster bleibt durch `token-holen.bat` offen
11. Datei **`.env`** mit Notepad öffnen
12. Hinter `ODIDO_TOKEN=` den Token einfügen (eine Zeile, ohne Leerzeichen/Anführungszeichen)
13. Speichern

**Tipp:** Nicht nur „Y“ drücken und wegschauen — erst Token kopieren, dann Fenster schließen.

Wenn das Programm später meldet, der Token sei ungültig (401/403), Schritt 3 wiederholen.

---

### Schritt 4 — Testen (noch nichts nachladen)

1. Doppelklick auf **`testen.bat`**
2. Im Fenster sollte ungefähr stehen, wie viele MB noch übrig sind  
3. Es steht dabei **DRY-RUN** — es wird **nichts** nachgeladen

Wenn hier schon ein Fehler kommt:

| Meldung | Was tun |
| --- | --- |
| Kein Token / Token fehlt | `.env` prüfen, `ODIDO_TOKEN=` ausfüllen |
| 401 / 403 | Token neu holen (Schritt 3) |
| Keine Subscription | `ODIDO_MSISDN` prüfen (`+31…`) |
| Python nicht gefunden | Schritt 1 nochmal, PATH-Haken setzen |

---

### Schritt 5 — Automatisch laufen lassen

Wenn der Test okay war:

1. Doppelklick auf **`starten.bat`**
2. Das Fenster **offen lassen**
3. Das Programm prüft alle paar Minuten und lädt bei Bedarf **gratis** nach
4. Beenden: Fenster anklicken und **Strg + C**, oder Fenster schließen

Solange du an dem Tag viel herunterlädst, lass `starten.bat` einfach mitlaufen.

---

## Was passiert hinter den Kulissen? (kurz)

```text
PC (dieses Programm)  →  fragt Odido: „Wie viel GB sind noch da?“
                      →  wenn wenig übrig: „Bitte gratis 2 GB“ (Code A0DAY01)
ZTE-Router            →  macht nur Internet, keine Auffüllung
```

Es werden **keine bezahlten** Pakete gekauft. Im Programm ist fest verdrahtet: nur der gratis-Code.

---

## Häufige Fragen

**Warum stockt das Internet trotzdem kurz?**  
Odido erlaubt den nächsten Aanvuller oft erst, wenn vom aktuellen noch **wenig** übrig ist (rund unter 350 MB). Kurz langsamer werden kann normal sein — danach sollte es wieder schnell gehen.

**Gilt der Aanvuller den ganzen Tag?**  
Ja, typischerweise bis **23:59 Uhr** am selben Tag (Niederlande). Am nächsten Tag startest du wieder mit dem normalen Tagesguthaben.

**Kann das Geld kosten?**  
Nur wenn du **kein** Unlimited mit gratis Aanvuller hast. Bei Unlimited Fair Use: nein. Das Programm kauft bewusst **keine** kostenpflichtigen Pakete.

**Muss der PC die ganze Nacht an sein?**  
Nur wenn du in der Zeit weiter viel Daten verbrauchst und automatisch nachgeladen werden soll. Sonst reicht: einschalten, wenn du große Downloads planst.

**Ist das erlaubt?**  
Odido selbst sagt, du darfst die gratis Aanvullers so oft aktivieren wie du willst. Automatisierung über die App-Schnittstelle ist **nicht offiziell** und kann gegen Nutzungsbedingungen verstoßen. Nutzung auf eigene Verantwortung.

---

## Dateien im Überblick

| Datei | Wofür |
| --- | --- |
| `einrichten.bat` | Einmalig vorbereiten |
| `starten-sms.bat` | **SMS-Automatik** (ZTE, ohne Token) |
| `testen-sms.bat` | SMS-Login testen (Dry-Run) |
| `sms-extra-jetzt.bat` | Einmal EXTRA an 1280 senden |
| `token-holen.bat` | Zugangscode holen (Fenster bleibt offen) |
| `testen.bat` | API-Variante prüfen, ohne nachzuladen |
| `starten.bat` | API-Automatik starten |
| `.env` | Einstellungen (Router-Passwort / Token) — **geheim halten** |
| `ANLEITUNG.md` | Diese Anleitung |

---

## Hilfe zum Token (Alternative)

Es gibt auch ein aktuelles Fertig-Programm von der Community (Windows-Datei, Stand Sept. 2026):  
https://github.com/lodu/odido-bundle-replenisher/releases/latest  

Dort unter Assets: **`odido-bundle-replenisher-windows.zip`**.  
Das kann beim ersten Start die Anmeldung selbst führen. Unser Ordner hier bleibt die einfache Python-Variante mit den `.bat`-Dateien oben.
