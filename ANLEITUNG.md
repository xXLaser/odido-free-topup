# Odido Fair Use — Guthaben automatisch gratis nachladen

**Geprüft am: 11. September 2026**

Diese Anleitung ist für Leute gedacht, die **keinen IT-Hintergrund** haben.  
Du brauchst einen normalen Windows-PC und deine Odido-SIM (z. B. im ZTE-Router).

---

## Was macht das Programm?

Bei Odido **Unlimited** bekommst du jeden Tag **20 GB** schnelles Internet in den Niederlanden.  
Sind die fast leer, darfst du **so oft du willst kostenlos 2 GB nachladen** („Aanvuller“).

Normalerweise machst du das per Hand in der Odido-App.  
Dieses Programm prüft auf dem PC regelmäßig: „Wie viel GB sind noch übrig?“  
Wenn wenig übrig ist, lädt es **automatisch nach — aber nur, wenn es gratis ist**.

| Was | Antwort |
| --- | --- |
| Kostet das Nachladen etwas? | **Nein.** Es wird nur der kostenlose 2‑GB-Aanvuller angefordert. |
| Muss ich am Router etwas umbauen? | **Nein.** Der ZTE-Router bleibt wie er ist. |
| Wo läuft das Programm? | Auf deinem **PC** (nicht im Router). |
| Wann brauche ich es? | Wenn du an einem Tag **mehr als 20 GB** brauchst (z. B. große Downloads). |

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

1. Windows-PC mit Internet (über den ZTE-Router ist okay)
2. Odido-Login (E-Mail/Passwort oder wie du dich sonst anmeldest)
3. Die **Handynummer der SIM** im Router (beginnt oft mit `+316…`)
4. **Python** (kostenlose Software) — Installation siehe Schritt 1

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
| `token-holen.bat` | Zugangscode holen (Fenster bleibt offen) |
| `testen.bat` | Sicher prüfen, ohne nachzuladen |
| `starten.bat` | Automatik starten |
| `.env` | Deine persönlichen Einstellungen (Token, Nummer) — **geheim halten** |
| `ANLEITUNG.md` | Diese Anleitung |
| `odido_free_topup.py` | Das eigentliche Programm |

---

## Hilfe zum Token (Alternative)

Es gibt auch ein aktuelles Fertig-Programm von der Community (Windows-Datei, Stand Sept. 2026):  
https://github.com/lodu/odido-bundle-replenisher/releases/latest  

Dort unter Assets: **`odido-bundle-replenisher-windows.zip`**.  
Das kann beim ersten Start die Anmeldung selbst führen. Unser Ordner hier bleibt die einfache Python-Variante mit den `.bat`-Dateien oben.
