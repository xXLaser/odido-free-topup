#!/usr/bin/env python3
"""Schreibt ODIDO_TOKEN und ODIDO_MSISDN in .env."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def upsert(text: str, key: str, value: str) -> str:
    line = f"{key}={value}"
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.M)
    if pattern.search(text):
        return pattern.sub(line, text)
    if text and not text.endswith("\n"):
        text += "\n"
    return text + line + "\n"


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: token_speichern.py <token> <msisdn>")
        return 1
    token = sys.argv[1].strip().strip('"').strip("'")
    msisdn = sys.argv[2].strip().strip('"').strip("'")
    if msisdn and not msisdn.startswith("+"):
        msisdn = "+" + msisdn.lstrip("0")
    # Falls jemand die URL eingefuegt hat: token= aus Query ziehen
    if "loginappresult" in token or "token=" in token.lower():
        m = re.search(r"[?&]token=([^&\s]+)", token, flags=re.I)
        if m:
            print("Hinweis: URL erkannt — Query-Token extrahiert.")
            print("Falls testen.bat 401 liefert, brauchst du den Bearer aus dem Authenticator (nach Y).")
            token = m.group(1)

    path = Path(__file__).resolve().parent / ".env"
    text = path.read_text(encoding="utf-8") if path.is_file() else (
        Path(__file__).resolve().parent / ".env.example"
    ).read_text(encoding="utf-8")
    text = upsert(text, "ODIDO_TOKEN", token)
    text = upsert(text, "ODIDO_MSISDN", msisdn)
    path.write_text(text, encoding="utf-8")
    print(f"Geschrieben: {path}")
    print(f"ODIDO_MSISDN={msisdn}")
    print(f"ODIDO_TOKEN Laenge={len(token)} Zeichen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
