"""ZTE MC888 / MC888 Pro client (LOGIN + SEND_SMS)."""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime
from typing import Any

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

log = logging.getLogger("zte")

# Neuere Firmwares (MC888 Pro ABPL): zsidn — aeltere: stok
SESSION_COOKIE_NAMES = ("zsidn", "stok", "random")


def _sha256_upper(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest().upper()


class ZteRouter:
    """MC888 / MC888 Pro goform client."""

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
        # Rueckwaertskompatibel fuer aelteren Code
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
        h = {
            "Referer": self.base,
            "Origin": self.base.rstrip("/"),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
        }
        if with_cookie and self.cookie_value:
            # Wie vom Router gesetzt: Name="VALUE"
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
        return self.session.post(
            f"{self.base}goform/goform_set_cmd_process",
            data=data,
            headers=self._headers(with_cookie=bool(self.cookie_value)),
            timeout=self.timeout,
            verify=False,
        )

    def _field(self, name: str) -> str:
        data = self._get({"isTest": "false", "cmd": name})
        val = data.get(name)
        return "" if val is None else str(val)

    def _password_hash(self, ld: str) -> str:
        prefix = _sha256_upper(self.password)
        return _sha256_upper(prefix + ld.upper())

    def _ad_token(self, rd: str) -> str:
        prefix = _sha256_upper(self.wa + self.cr)
        return _sha256_upper(prefix + rd.upper())

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
                        values.extend(fn("set-cookie") or [])
                    except Exception:
                        pass
        if not values:
            for key in response.headers:
                if key.lower() == "set-cookie":
                    values.append(response.headers[key])
        return values

    def _pick_session_cookie(self, response: requests.Response) -> tuple[str, str] | None:
        """Return (cookie_name, cookie_value) from Set-Cookie / jars."""
        for sc in self._iter_set_cookie_headers(response):
            for name in SESSION_COOKIE_NAMES:
                m = re.search(
                    rf"\b{re.escape(name)}\s*=\s*\"?([^\";,\s]+)\"?",
                    sc or "",
                    flags=re.I,
                )
                if m:
                    return name.lower(), m.group(1).strip().strip('"')

        self.session.cookies.update(response.cookies)
        jar = {**response.cookies.get_dict(), **self.session.cookies.get_dict()}
        for name in SESSION_COOKIE_NAMES:
            if name in jar and jar[name]:
                return name, str(jar[name]).strip().strip('"')
            # case variants
            for k, v in jar.items():
                if k.lower() == name and v:
                    return name, str(v).strip().strip('"')
        return None

    def _set_session(self, name: str, value: str) -> None:
        self.cookie_name = name
        self.cookie_value = value
        self.stok = value  # alias
        # requests jar ohne ueberfluessige Anfuehrungszeichen
        self.session.cookies.set(name, value, path="/")

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
            raise RuntimeError("Konnte LD nicht lesen — Router erreichbar?")

        hashed = self._password_hash(ld)
        log.debug("LD=%s... hash_prefix=%s...", ld[:8], hashed[:8])

        attempts: list[dict[str, str]] = [
            {"isTest": "false", "goformId": "LOGIN", "password": hashed},
        ]
        if self.username:
            attempts.append(
                {
                    "isTest": "false",
                    "goformId": "LOGIN",
                    "password": hashed,
                    "user": self.username,
                }
            )

        last_result = ""
        last_body = ""
        for payload in attempts:
            self.cookie_value = None
            self.stok = None
            r = self.session.post(
                f"{self.base}goform/goform_set_cmd_process",
                data=payload,
                headers={
                    "Referer": self.base,
                    "Origin": self.base.rstrip("/"),
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "X-Requested-With": "XMLHttpRequest",
                },
                timeout=self.timeout,
                verify=False,
            )
            last_body = (r.text or "")[:200]
            try:
                data = r.json()
            except Exception:
                data = {}
            last_result = str(data.get("result", ""))
            picked = self._pick_session_cookie(r)
            set_cookies = self._iter_set_cookie_headers(r)
            log.debug(
                "Login goformId=%s result=%s cookie=%s set-cookie=%r",
                payload.get("goformId"),
                last_result,
                f"{picked[0]}={picked[1][:12]}..." if picked else "no",
                set_cookies,
            )

            if last_result == "3":
                raise RuntimeError(
                    "Router-Session belegt (result=3). "
                    "Browser-Tab mit 192.168.0.1 SCHLIESSEN, 10 Sekunden warten, dann erneut."
                )

            if last_result == "0":
                if not picked:
                    self.session.get(
                        f"{self.base}index.html",
                        headers={"Referer": self.base},
                        timeout=self.timeout,
                        verify=False,
                    )
                    jar = self.session.cookies.get_dict()
                    for name in SESSION_COOKIE_NAMES:
                        if name in jar and jar[name]:
                            picked = (name, str(jar[name]).strip().strip('"'))
                            break

                if not picked:
                    raise RuntimeError(
                        "Login result=0, aber kein Session-Cookie (zsidn/stok). "
                        f"Set-Cookie: {set_cookies!r}"
                    )

                name, value = picked
                self._set_session(name, value)
                rd = self._field("RD")
                self._ad = self._ad_token(rd)
                log.info("ZTE-Login OK (%s)", name)
                return value

            if last_result == "1":
                break

        hint = ""
        if last_result == "1":
            hint = (
                " result=1 = falsches Passwort. "
                "Admin-/Website-Passwort vom Aufkleber (nicht WLAN)."
            )
        raise RuntimeError(
            f"ZTE-Login fehlgeschlagen (result={last_result or '?'}).{hint} Antwort: {last_body}"
        )

    def send_sms(self, number: str, message: str, cookie: str | None = None) -> dict[str, Any]:
        if not self.cookie_value or not self._ad:
            self.login()
        assert self._ad is not None

        now = datetime.now().astimezone()
        offset_h = int(now.utcoffset().total_seconds() // 3600) if now.utcoffset() else 1
        sms_time = (
            f"{now.year % 100:02d};{now.month:02d};{now.day:02d};"
            f"{now.hour:02d};{now.minute:02d};{now.second:02d};+{abs(offset_h)}"
        )
        body = message.encode("utf-16-be").hex().upper()

        try:
            rd = self._field("RD")
            if rd:
                self._ad = self._ad_token(rd)
        except Exception:
            pass

        variants = [
            {
                "isTest": "false",
                "goformId": "SEND_SMS",
                "Number": number,
                "sms_time": sms_time,
                "MessageBody": body,
                "encode_type": "UNICODE",
                "AD": self._ad,
            },
            {
                "isTest": "false",
                "goformId": "SEND_SMS",
                "notCallback": "true",
                "Number": number,
                "sms_time": sms_time,
                "MessageBody": body,
                "ID": "-1",
                "encode_type": "UNICODE",
                "AD": self._ad,
            },
            {
                "isTest": "false",
                "goformId": "SEND_SMS",
                "Number": number,
                "sms_time": sms_time.rsplit(";", 1)[0] + ";+0",
                "MessageBody": body,
                "encode_type": "UNICODE",
                "AD": self._ad,
            },
        ]

        last: dict[str, Any] = {}
        for data in variants:
            r = self._post(data)
            try:
                last = r.json()
            except Exception:
                last = {"raw": r.text, "status_code": r.status_code}
            log.debug("SEND_SMS -> %s", last)
            result = str(last.get("result", "")).lower()
            if result in ("success", "0", "ok"):
                return last
        return last

    def list_sms(self, cookie: str | None = None, mem_store: int = 1) -> list[dict[str, Any]]:
        if not self.cookie_value:
            self.login()
        for cmd in ("sms_data_total", "sms_data_info"):
            try:
                r = self.session.get(
                    f"{self.base}goform/goform_get_cmd_process",
                    params={
                        "isTest": "false",
                        "cmd": cmd,
                        "page": "0",
                        "data_per_page": "50",
                        "mem_store": str(mem_store),
                        "tags": "10",
                        "order_by": "order by id desc",
                    },
                    headers=self._headers(),
                    timeout=self.timeout,
                    verify=False,
                )
                r.raise_for_status()
                data = r.json()
                messages = data.get("messages") or data.get("Messages") or []
                if isinstance(messages, dict):
                    messages = list(messages.values())
                if messages or cmd == "sms_data_info":
                    return list(messages)
            except Exception as e:
                log.debug("list_sms %s: %s", cmd, e)
        return []
