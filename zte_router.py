"""ZTE MC888 / MC888 Pro client (LOGIN + SEND_SMS)."""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime
from typing import Any
from urllib.parse import quote

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

log = logging.getLogger("zte")

SESSION_COOKIE_NAMES = ("zsidn", "stok", "random")


def _sha256_upper(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest().upper()


def _md5_lower(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest().lower()


def _md5_upper(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest().upper()


class ZteRouter:
    def __init__(
        self,
        host: str,
        password: str,
        username: str | None = "",
        timeout: float = 20.0,
    ) -> None:
        self.host = host.strip().removeprefix("http://").removeprefix("https://").rstrip("/")
        self.password = password.strip().strip('"').strip("'")
        self.username = (username or "").strip()
        self.timeout = timeout
        self.session = requests.Session()
        self.base = f"http://{self.host}/"
        self.wa = ""
        self.cr = ""
        self.cookie_name = "zsidn"
        self.cookie_value: str | None = None
        self._ad: str | None = None
        self.stok: str | None = None
        self._probe()

    def _probe(self) -> None:
        for scheme in ("http", "https"):
            try:
                r = self.session.get(f"{scheme}://{self.host}/", timeout=5, verify=False)
                if r.ok or r.status_code in (401, 403, 302):
                    self.base = f"{scheme}://{self.host}/"
                    return
            except requests.RequestException:
                continue

    def _headers(self, with_cookie: bool = True) -> dict[str, str]:
        # Wichtig: Cookie NUR hier setzen, nicht zusaetzlich im Cookie-Jar
        # (sonst doppelte/kaputte Cookies bei manchen Firmwares).
        h = {
            "Referer": f"{self.base}index.html",
            "Origin": self.base.rstrip("/"),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        if with_cookie and self.cookie_value:
            h["Cookie"] = f'{self.cookie_name}="{self.cookie_value}"'
        return h

    def _get(self, params: dict[str, str]) -> dict[str, Any]:
        r = self.session.get(
            f"{self.base}goform/goform_get_cmd_process",
            params=params,
            headers=self._headers(with_cookie=bool(self.cookie_value)),
            timeout=self.timeout,
            verify=False,
        )
        r.raise_for_status()
        return r.json()

    def _post(self, data: dict[str, str]) -> requests.Response:
        # requests soll KEINE Jar-Cookies mitschicken
        return self.session.post(
            f"{self.base}goform/goform_set_cmd_process",
            data=data,
            headers=self._headers(with_cookie=bool(self.cookie_value)),
            cookies={},  # Jar unterdruecken
            timeout=self.timeout,
            verify=False,
        )

    def _field(self, name: str) -> str:
        data = self._get({"isTest": "false", "cmd": name})
        val = data.get(name)
        return "" if val is None else str(val)

    def _password_hash(self, ld: str) -> str:
        return _sha256_upper(_sha256_upper(self.password) + ld.upper())

    def _ad_candidates(self, rd: str) -> list[tuple[str, str]]:
        """Alle gaengigen AD-Varianten (SHA256 und MD5, Reihenfolge wa/cr)."""
        rd_u = rd.upper()
        rd_raw = rd
        cands = [
            ("sha256(wa+cr)+rdU", _sha256_upper(_sha256_upper(self.wa + self.cr) + rd_u)),
            ("sha256(cr+wa)+rdU", _sha256_upper(_sha256_upper(self.cr + self.wa) + rd_u)),
            ("sha256(wa+cr)+rd", _sha256_upper(_sha256_upper(self.wa + self.cr) + rd_raw)),
            ("md5(cr+wa)+rdU", _md5_upper(_md5_lower(self.cr + self.wa) + rd_u)),
            ("md5(wa+cr)+rdU", _md5_upper(_md5_lower(self.wa + self.cr) + rd_u)),
            ("md5(cr+wa)+rd", _md5_upper(_md5_lower(self.cr + self.wa) + rd_raw)),
            ("md5U(cr+wa)+rdU", _md5_upper(_md5_upper(self.cr + self.wa) + rd_u)),
        ]
        out: list[tuple[str, str]] = []
        seen: set[str] = set()
        for label, val in cands:
            if val not in seen:
                seen.add(val)
                out.append((label, val))
        return out

    def _iter_set_cookie_headers(self, response: requests.Response) -> list[str]:
        values: list[str] = []
        raw = getattr(response, "raw", None)
        headers = getattr(raw, "headers", None) if raw is not None else None
        if headers is not None:
            for getter in ("get_all", "getlist"):
                fn = getattr(headers, getter, None)
                if callable(fn):
                    try:
                        values.extend(fn("Set-Cookie") or [])
                    except Exception:
                        pass
        if not values:
            for key in response.headers:
                if key.lower() == "set-cookie":
                    values.append(response.headers[key])
        return values

    def _pick_session_cookie(self, response: requests.Response) -> tuple[str, str] | None:
        for sc in self._iter_set_cookie_headers(response):
            for name in SESSION_COOKIE_NAMES:
                m = re.search(
                    rf"\b{re.escape(name)}\s*=\s*\"?([^\";,\s]+)\"?",
                    sc or "",
                    flags=re.I,
                )
                if m:
                    return name.lower(), m.group(1).strip().strip('"')
        return None

    def _set_session(self, name: str, value: str) -> None:
        self.cookie_name = name
        self.cookie_value = value.strip().strip('"')
        self.stok = self.cookie_value
        # Jar leeren — wir setzen Cookie nur per Header
        self.session.cookies.clear()

    def login(self) -> str:
        info = self._get(
            {
                "isTest": "false",
                "cmd": "Language,cr_version,wa_inner_version",
                "multi_data": "1",
            }
        )
        self.cr = str(info.get("cr_version") or self._field("cr_version"))
        self.wa = str(info.get("wa_inner_version") or self._field("wa_inner_version"))
        log.info("Router: %s", self.wa)

        ld = self._field("LD")
        if not ld:
            raise RuntimeError("Konnte LD nicht lesen")

        hashed = self._password_hash(ld)
        self.cookie_value = None
        r = self.session.post(
            f"{self.base}goform/goform_set_cmd_process",
            data={"isTest": "false", "goformId": "LOGIN", "password": hashed},
            headers={
                "Referer": f"{self.base}index.html",
                "Origin": self.base.rstrip("/"),
                "X-Requested-With": "XMLHttpRequest",
            },
            cookies={},
            timeout=self.timeout,
            verify=False,
        )
        try:
            data = r.json()
        except Exception:
            data = {}
        result = str(data.get("result", ""))
        picked = self._pick_session_cookie(r)
        log.debug(
            "Login result=%s cookie=%s set-cookie=%r",
            result,
            f"{picked[0]}={picked[1][:12]}..." if picked else "no",
            self._iter_set_cookie_headers(r),
        )

        if result == "3":
            raise RuntimeError(
                "Session belegt (result=3). Browser-Tab 192.168.0.1 schliessen, warten, erneut."
            )
        if result == "1":
            raise RuntimeError(
                "Falsches Passwort (result=1). Website-Passwort vom Aufkleber, nicht WLAN."
            )
        if result != "0" or not picked:
            raise RuntimeError(f"Login fehlgeschlagen result={result} cookie={picked} body={r.text[:200]}")

        self._set_session(*picked)
        rd = self._field("RD")
        ads = self._ad_candidates(rd)
        self._ad = ads[0][1]
        self._ads = ads
        log.info("ZTE-Login OK (%s)", picked[0])
        return self.cookie_value or ""

    def sms_capacity(self) -> dict[str, Any]:
        try:
            return self._get({"isTest": "false", "cmd": "sms_capacity_info"})
        except Exception as e:
            return {"error": str(e)}

    def send_sms(self, number: str, message: str, cookie: str | None = None) -> dict[str, Any]:
        if not self.cookie_value:
            self.login()

        # Kapazitaet loggen (voller Speicher = oft failure)
        cap = self.sms_capacity()
        log.info("SMS-Speicher: %s", cap)

        now = datetime.now().astimezone()
        offset_h = int(now.utcoffset().total_seconds() // 3600) if now.utcoffset() else 2
        sms_time = (
            f"{now.year % 100:02d};{now.month:02d};{now.day:02d};"
            f"{now.hour:02d};{now.minute:02d};{now.second:02d};+{abs(offset_h)}"
        )
        body_unicode = message.encode("utf-16-be").hex().upper()
        # GSM7: Zeichen-Index als Hex (einfache Variante)
        gsm = (
            "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
            "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ¿abcdefghijklmnopqrstuvwxyzäöñüà"
        )
        body_gsm = "".join(f"{gsm.find(c):02X}" if c in gsm else "3F" for c in message)

        rd = self._field("RD")
        ads = self._ad_candidates(rd)
        numbers = [number, quote(number)]
        times = [sms_time, sms_time.rsplit(";", 1)[0] + ";+0", sms_time.rsplit(";", 1)[0] + ";+1"]

        last: dict[str, Any] = {}
        for ad_label, ad in ads:
            for num in numbers:
                for t in times:
                    for encode_type, body in (
                        ("UNICODE", body_unicode),
                        ("GSM7_default", body_gsm),
                        ("GSM7_default", body_unicode),  # manche wollen trotzdem UCS2-Hex
                    ):
                        for extra in (
                            {},
                            {"notCallback": "true", "ID": "-1"},
                        ):
                            data = {
                                "isTest": "false",
                                "goformId": "SEND_SMS",
                                "Number": num,
                                "sms_time": t,
                                "MessageBody": body,
                                "encode_type": encode_type,
                                "AD": ad,
                                **extra,
                            }
                            r = self._post(data)
                            try:
                                last = r.json()
                            except Exception:
                                last = {"raw": r.text, "status_code": r.status_code}
                            result = str(last.get("result", "")).lower()
                            log.debug(
                                "SEND_SMS ad=%s enc=%s num=%s -> %s",
                                ad_label,
                                encode_type,
                                num,
                                last,
                            )
                            if result in ("success", "0", "ok", "sucess"):
                                log.info("SMS OK (ad=%s enc=%s)", ad_label, encode_type)
                                self._ad = ad
                                return last

        return last or {"result": "failure"}

    def list_sms(self, cookie: str | None = None, mem_store: int = 1) -> list[dict[str, Any]]:
        if not self.cookie_value:
            self.login()
        for cmd in ("sms_data_total", "sms_data_info"):
            try:
                data = self._get(
                    {
                        "isTest": "false",
                        "cmd": cmd,
                        "page": "0",
                        "data_per_page": "50",
                        "mem_store": str(mem_store),
                        "tags": "10",
                        "order_by": "order by id desc",
                    }
                )
                messages = data.get("messages") or data.get("Messages") or []
                if isinstance(messages, dict):
                    messages = list(messages.values())
                if messages or cmd == "sms_data_info":
                    return list(messages)
            except Exception as e:
                log.debug("list_sms %s: %s", cmd, e)
        return []
