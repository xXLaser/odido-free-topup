#!/usr/bin/env python3
"""SMS-Diagnose fuer ZTE-Router."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from odido_sms_topup import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("diagnose")

from zte_router import ZteRouter  # noqa: E402


def main() -> int:
    host = os.environ.get("ZTE_HOST", "192.168.0.1")
    password = os.environ.get("ZTE_PASSWORD", "")
    user = os.environ.get("ZTE_USER", "")
    if not password:
        log.error("ZTE_PASSWORD fehlt in .env")
        return 1

    router = ZteRouter(host, password, user)
    try:
        router.login()
    except Exception as e:
        log.error("Login: %s", e)
        return 2

    print("--- SMS CAPACITY ---")
    print(router.sms_capacity())
    print("--- INBOX ---")
    try:
        msgs = router.list_sms()
        if not msgs:
            print("(leer oder nicht lesbar)")
        for m in msgs:
            print(m)
    except Exception as e:
        print("Inbox-Fehler:", e)
    print("--- HINT ---")
    print("Wenn auch in der Router-Weboberflaeche kein SMS versendet werden kann,")
    print("funktioniert die SMS-Variante (EXTRA an 1280) auf diesem Geraet/SIM nicht.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
