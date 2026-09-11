#!/usr/bin/env python3
"""
Odido Unlimited — gratis 2 GB Fair-Use-Aanvuller automatisch anfordern.

Läuft auf dem PC (nicht auf dem ZTE-Router). Prüft regelmäßig das Restguthaben
über die Odido Customer API und fordert NUR den kostenlosen NL-Aanvuller
(BuyingCode A0DAY01) an — niemals bezahlte Bundles.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    print("Bitte zuerst installieren:  pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

# Nur dieser Code = gratis 2 GB NL (Unlimited Fair Use). Niemals ändern ohne Absicht.
FREE_BUYING_CODE = "A0DAY01"
API_BASE = "https://capi.odido.nl"
LINKED_SUBS_PATH = "/c88084b603f5/linkedsubscriptions"
# An aktuelle Odido-App angelehnt (Stand 2026, wie in Community-Tools).
USER_AGENT = "ODIDO 8.0.0 (Android 12; 12)"

# Nächster Aanvuller oft erst bei wenig Rest. Zu hoch → Odido lehnt ab.
DEFAULT_THRESHOLD_MB = 350
DEFAULT_INTERVAL_SEC = 120


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def setup_logging(verbose: bool) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("odido")


def api_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def get_subscription_url(session: requests.Session, token: str, msisdn: str | None) -> str:
    url = API_BASE + LINKED_SUBS_PATH
    r = session.get(url, headers=api_headers(token), timeout=30)
    r.raise_for_status()
    data = r.json()
    subs = data.get("subscriptions") or data.get("Subscriptions") or []
    if not subs:
        raise RuntimeError("Keine Subscriptions gefunden — Token oder Account prüfen.")

    if msisdn:
        needle = msisdn.replace(" ", "")
        for sub in subs:
            for key in ("MSISDN", "Msisdn", "msisdn", "PhoneNumber"):
                val = str(sub.get(key, "")).replace(" ", "")
                if val and (val == needle or val.endswith(needle.lstrip("+0"))):
                    return sub["SubscriptionURL"] if "SubscriptionURL" in sub else sub["subscriptionURL"]
        raise RuntimeError(f"Keine Subscription für MSISDN {msisdn} gefunden.")

    sub = subs[0]
    return sub.get("SubscriptionURL") or sub["subscriptionURL"]


def remaining_nl_mb(bundles: list[dict[str, Any]]) -> float:
    total = 0
    for bundle in bundles:
        zone = bundle.get("ZoneColor") or bundle.get("zoneColor") or ""
        if zone.upper() != "NL":
            continue
        rem = bundle.get("Remaining") or bundle.get("remaining") or {}
        value = rem.get("Value") if isinstance(rem, dict) else rem
        if value is None:
            continue
        # API liefert typischerweise KB
        total += int(value)
    return round(total / 1024, 1)


def fetch_bundles(session: requests.Session, token: str, sub_url: str) -> list[dict[str, Any]]:
    r = session.get(f"{sub_url}/roamingbundles", headers=api_headers(token), timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("Bundles") or data.get("bundles") or []


def assert_free_only(buying_code: str) -> None:
    if buying_code != FREE_BUYING_CODE:
        raise RuntimeError(
            f"Sicherheitsstopp: BuyingCode {buying_code!r} ist nicht der gratis Aanvuller "
            f"({FREE_BUYING_CODE}). Abbruch — keine bezahlten Bundles."
        )


def request_free_topup(session: requests.Session, token: str, sub_url: str, log: logging.Logger) -> None:
    assert_free_only(FREE_BUYING_CODE)
    payload = {"Bundles": [{"BuyingCode": FREE_BUYING_CODE}]}
    log.info("Fordere gratis 2 GB Aanvuller an (nur %s)…", FREE_BUYING_CODE)
    r = session.post(
        f"{sub_url}/roamingbundles",
        headers=api_headers(token),
        data=json.dumps(payload),
        timeout=30,
    )
    if not r.ok:
        body = r.text[:500]
        log.error("Auffüllen fehlgeschlagen: %s %s — %s", r.status_code, r.reason, body)
        r.raise_for_status()
    log.info("Gratis-Aanvuller erfolgreich angefordert.")
    log.debug("Antwort: %s", r.text[:300])


def check_once(
    session: requests.Session,
    token: str,
    msisdn: str | None,
    threshold_mb: float,
    log: logging.Logger,
    dry_run: bool,
) -> None:
    sub_url = get_subscription_url(session, token, msisdn)
    log.debug("Subscription URL: %s", sub_url)
    bundles = fetch_bundles(session, token, sub_url)
    left = remaining_nl_mb(bundles)
    log.info("NL-Restguthaben: %.0f MB (Schwellwert: %.0f MB)", left, threshold_mb)

    if left >= threshold_mb:
        log.info("Ausreichend Guthaben — nichts zu tun.")
        return

    if dry_run:
        log.warning("DRY-RUN: würde jetzt gratis Auffüllen, tut es aber nicht.")
        return

    request_free_topup(session, token, sub_url, log)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Odido Unlimited: nur gratis 2 GB Fair-Use-Aanvuller automatisch nachladen."
    )
    p.add_argument(
        "--token",
        default=os.environ.get("ODIDO_TOKEN") or os.environ.get("AUTHORIZATION_TOKEN"),
        help="Bearer-Token (oder Env ODIDO_TOKEN)",
    )
    p.add_argument(
        "--msisdn",
        default=os.environ.get("ODIDO_MSISDN") or os.environ.get("MSISDN"),
        help="Rufnummer der SIM, z.B. +31612345678 (optional bei nur einer Sub)",
    )
    p.add_argument(
        "--threshold-mb",
        type=float,
        default=float(os.environ.get("ODIDO_THRESHOLD", DEFAULT_THRESHOLD_MB)),
        help=f"Auffüllen unter diesem Rest in MB (Default {DEFAULT_THRESHOLD_MB})",
    )
    p.add_argument(
        "--interval",
        type=int,
        default=int(os.environ.get("ODIDO_INTERVAL", DEFAULT_INTERVAL_SEC)),
        help=f"Prüfintervall in Sekunden (Default {DEFAULT_INTERVAL_SEC})",
    )
    p.add_argument("--once", action="store_true", help="Nur einmal prüfen und beenden")
    p.add_argument("--dry-run", action="store_true", help="Nur prüfen, nicht auffüllen")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args()


def main() -> int:
    load_dotenv(Path(__file__).resolve().parent / ".env")
    # Args nach .env nochmal lesen, falls Defaults aus Env kommen sollen
    args = parse_args()
    log = setup_logging(args.verbose)

    if not args.token:
        log.error(
            "Kein Token. Setze ODIDO_TOKEN in .env oder nutze --token.\n"
            "Token holen: Odido Authenticator — "
            "https://github.com/GuusBackup/Odido.Authenticator/releases/latest"
        )
        return 1

    if args.threshold_mb > 2000:
        log.warning(
            "Schwellwert > 2000 MB: Odido lehnt oft ab, solange noch viel vom Aanvuller übrig ist. "
            "Empfohlen: ~350 MB."
        )

    session = requests.Session()
    log.info(
        "Start — nur gratis Aanvuller %s | Schwellwert %.0f MB | Intervall %ss%s",
        FREE_BUYING_CODE,
        args.threshold_mb,
        args.interval,
        " | DRY-RUN" if args.dry_run else "",
    )

    while True:
        try:
            check_once(session, args.token, args.msisdn, args.threshold_mb, log, args.dry_run)
        except requests.HTTPError as e:
            log.error("HTTP-Fehler: %s", e)
            if e.response is not None and e.response.status_code in (401, 403):
                log.error("Token ungültig/abgelaufen — neu anmelden und ODIDO_TOKEN aktualisieren.")
                return 2
        except Exception as e:
            log.error("Fehler: %s", e, exc_info=args.verbose)

        if args.once:
            return 0
        time.sleep(max(30, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
