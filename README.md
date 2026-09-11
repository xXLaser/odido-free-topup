# Odido Free Top-up

Automatisch den **gratis** 2 GB Fair-Use-Aanvuller von Odido Unlimited nachladen.

**→ Anleitung:** [`ANLEITUNG.md`](ANLEITUNG.md)

## Zwei Varianten

### B) SMS über ZTE-Router (ohne Odido-Token) — empfohlen wenn Token hakt

1. `einrichten.bat`
2. In `.env`: `ZTE_HOST`, `ZTE_USER`, `ZTE_PASSWORD`
3. `testen-sms.bat` → `sms-extra-jetzt.bat` → `starten-sms.bat`

Sendet nur **`EXTRA` an `1280`** (laut Odido gratis 2 GB bei Unlimited).

### A) Odido-API mit Token

1. `einrichten.bat`
2. Token + MSISDN in `.env`
3. `testen.bat` → `starten.bat`
