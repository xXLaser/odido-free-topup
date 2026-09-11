#!/usr/bin/env python3
"""
Odido Unlimited — gratis 2 GB per SMS uber den ZTE-Router.

Odido-Support: SMS-Text EXTRA an Kurzwahl 1280 (gratis Aanvuller bei Unlimited).
Kein Odido-App-Token noetig. Laeuft auf dem PC im LAN hinter dem Router.
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("Bitte zuerst: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

from zte_router import ZteRouter

# Fest verdrahtet: nur der gratis Unlimited-Aanvuller per SMS.
FREE_SMS_NUMBER = "1280"
FREE_SMS_TEXT = "EXTRA"

# Wenn Odido eine Hinweis-SMS schickt, danach EXTRA senden.
INBOX_HINTS = (
    "aanvull",
    "2 gb",
    "2gb",
    "databundel",
    "dagtegoed",
    "bijna op",
    "op is",
    "unlimited",
    "extra gb",
    "mb's",
    "mbs",
)


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def setup_logging(verbose: bool) -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("odido-sms")


def decode_sms_content(raw: str) -> str:
    """ZTE liefert Unicode oft als UTF-16BE-Hex."""
    if not raw:
        return ""
    s = raw.strip()
    if re.fullmatch(r"[0-9A-Fa-f]+", s) and len(s) % 4 == 0:
        try:
            return bytes.fromhex(s).decode("utf-16-be", errors="ignore")
        except Exception:
            pass
    return s


def looks_like_topup_hint(text: str) -> bool:
    t = text.lower()
    return any(h in t for h in INBOX_HINTS)


def send_free_extra(router: ZteRouter, log: logging.Logger, dry_run: bool) -> None:
    log.info("Sende gratis Aanvuller: SMS '%s' -> %s", FREE_SMS_TEXT, FREE_SMS_NUMBER)
    if dry_run:
        log.warning("DRY-RUN: wuerde senden, tut es nicht.")
        return
    result = router.send_sms(FREE_SMS_NUMBER, FREE_SMS_TEXT)
    log.info("Router-Antwort: %s", result)


def process_inbox(router: ZteRouter, log: logging.Logger, dry_run: bool, seen: set[str]) -> bool:
    """Returns True if EXTRA was triggered."""
    try:
        messages = router.list_sms()
    except Exception as e:
        log.error("SMS-Posteingang lesen fehlgeschlagen: %s", e)
        return False

    triggered = False
    for msg in messages:
        mid = str(msg.get("id") or msg.get("ID") or msg.get("tag") or "")
        number = str(msg.get("number") or msg.get("Number") or "")
        content = decode_sms_content(str(msg.get("content") or msg.get("Content") or ""))
        key = mid or f"{number}:{content[:40]}"
        if key in seen:
            continue
        seen.add(key)
        if not content:
            continue
        log.debug("SMS von %s: %s", number, content[:120])
        if looks_like_topup_hint(content):
            log.warning("Odido-Hinweis erkannt von %s — sende EXTRA an 1280", number)
            send_free_extra(router, log, dry_run)
            triggered = True
            # Nur eine EXTRA pro Inbox-Durchlauf
            break
    return triggered


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Odido gratis 2GB per SMS (EXTRA an 1280) uber ZTE-Router."
    )
    p.add_argument("--host", default=os.environ.get("ZTE_HOST", "192.168.0.1"))
    p.add_argument("--user", default=os.environ.get("ZTE_USER", "admin"))
    p.add_argument("--password", default=os.environ.get("ZTE_PASSWORD", ""))
    p.add_argument(
        "--interval",
        type=int,
        default=int(os.environ.get("ZTE_INTERVAL", "120")),
        help="Posteingang pruefen alle N Sekunden",
    )
    p.add_argument(
        "--periodic-extra-minutes",
        type=int,
        default=int(os.environ.get("ZTE_PERIODIC_EXTRA_MINUTES", "0")),
        help="Optional: alle N Minuten EXTRA senden (0=aus). Vorsicht: nur bei Bedarf sinnvoll.",
    )
    p.add_argument("--once-extra", action="store_true", help="Einmal EXTRA an 1280 senden und beenden")
    p.add_argument("--list-sms", action="store_true", help="SMS-Posteingang anzeigen und beenden")
    p.add_argument("--once", action="store_true", help="Posteingang einmal pruefen und beenden")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args()


def main() -> int:
    load_dotenv(Path(__file__).resolve().parent / ".env")
    args = parse_args()
    log = setup_logging(args.verbose)

    if not args.password:
        log.error("ZTE_PASSWORD fehlt in .env oder --password")
        return 1

    router = ZteRouter(args.host, args.password, username=args.user or None)
    try:
        router.login()
    except Exception as e:
        log.error("Login fehlgeschlagen: %s", e)
        log.error("Pruefe ZTE_HOST / ZTE_USER / ZTE_PASSWORD und ob der PC im Router-WLAN/LAN ist.")
        return 2

    if args.list_sms:
        for msg in router.list_sms():
            content = decode_sms_content(str(msg.get("content") or msg.get("Content") or ""))
            number = msg.get("number") or msg.get("Number")
            print(f"[{number}] {content}")
        return 0

    if args.once_extra:
        send_free_extra(router, log, args.dry_run)
        return 0

    seen: set[str] = set()
    # Bestehende SMS nicht sofort alle als neu behandeln
    try:
        for msg in router.list_sms():
            mid = str(msg.get("id") or msg.get("ID") or msg.get("tag") or "")
            number = str(msg.get("number") or msg.get("Number") or "")
            content = decode_sms_content(str(msg.get("content") or msg.get("Content") or ""))
            seen.add(mid or f"{number}:{content[:40]}")
    except Exception as e:
        log.warning("Konnte Inbox nicht vorladen: %s", e)

    log.info(
        "SMS-Modus aktiv — nur gratis EXTRA->%s | Inbox alle %ss%s",
        FREE_SMS_NUMBER,
        args.interval,
        " | DRY-RUN" if args.dry_run else "",
    )

    last_periodic = 0.0
    while True:
        try:
            process_inbox(router, log, args.dry_run, seen)
            if args.periodic_extra_minutes > 0:
                now = time.time()
                if now - last_periodic >= args.periodic_extra_minutes * 60:
                    send_free_extra(router, log, args.dry_run)
                    last_periodic = now
        except requests.RequestException as e:
            log.error("Netzwerkfehler: %s — versuche Re-Login", e)
            try:
                router.login()
            except Exception as e2:
                log.error("Re-Login fehlgeschlagen: %s", e2)
        except Exception as e:
            log.error("Fehler: %s", e, exc_info=args.verbose)

        if args.once:
            return 0
        time.sleep(max(30, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
