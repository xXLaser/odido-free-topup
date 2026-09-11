"""ZTE consumer-router client — tuned for MC888 / MC888 Pro."""

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
        timeout: float = 15.0,
    ) -> None:
        self.host = host.strip().removeprefix("http://").removeprefix("https://").rstrip("/")
        self.password = password
        self.username = (username or "").strip()
        self.timeout = timeout
        self.session = requests.Session()
        self.base = f"http://{self.host}/"
        self._ad: str | None = None
        self._cookie: str | None = None
        self._probe()

    def _probe(self) -> None:
        for scheme in ("http", "https"):
            try:
                r = self.session.get(f"{scheme}://{self.host}/", timeout=5, verify=False)
                if r.ok or r.status_code in (401, 403, 302):
                    self.base = f"{scheme}://{self.host}/"
                    self.session.get(f"{self.base}index.html", timeout=5, verify=False)
                    return
            except requests.RequestException:
                continue

    def _headers(self) -> dict[str, str]:
        h = {
            "Referer": f"{self.base}index.html",
            "Origin": self.base.rstrip("/"),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
        }
        if self._cookie:
            h["Cookie"] = self._cookie
        return h

    def _capture_stok(self, response: requests.Response) -> str | None:
        # Prefer Set-Cookie header (quoted stok="...")
        raw = response.headers.get("Set-Cookie") or ""
        if not raw and "set-cookie" in getattr(response.headers, "getlist", lambda _x: [])("Set-Cookie") if False else "":
            pass
        # requests may split cookies; also check header string variants
        set_cookies = []
        if hasattr(response.headers, "get_list"):
            set_cookies = response.headers.get_list("Set-Cookie")
        elif "Set-Cookie" in response.headers:
            set_cookies = [response.headers["Set-Cookie"]]
        # urllib3 CookieConflict / multiple
        try:
            set_cookies = response.raw.headers.getlist("Set-Cookie")  # type: ignore[attr-defined]
        except Exception:
            if not set_cookies and response.headers.get("Set-Cookie"):
                set_cookies = [response.headers.get("Set-Cookie", "")]

        for sc in set_cookies:
            m = re.search(r"stok=([^;]+)", sc or "")
            if m:
                return m.group(1).strip().strip('"')

        for jar in (response.cookies, self.session.cookies):
            stok = jar.get("stok")
            if stok:
                return str(stok).strip().strip('"')
        return None

    def _set_cookie(self, stok: str | None) -> None:
        parts = []
        if stok:
            parts.append(f'stok="{stok}"')
        for c in self.session.cookies:
            if c.name.lower() != "stok":
                parts.append(f"{c.name}={c.value}")
        self._cookie = "; ".join(parts) if parts else None
        if stok:
            self.session.cookies.set("stok", stok, domain=self.host, path="/")

    def _get_json(self, params: dict[str, str]) -> dict[str, Any]:
        r = self.session.get(
            f"{self.base}goform/goform_get_cmd_process",
            params=params,
            headers=self._headers(),
            timeout=self.timeout,
            verify=False,
        )
        r.raise_for_status()
        return r.json()

    def _get_field(self, field: str) -> str:
        data = self._get_json({"isTest": "false", "cmd": field})
        val = data.get(field)
        return "" if val is None else str(val)

    def _post(self, data: dict[str, str]) -> requests.Response:
        return self.session.post(
            f"{self.base}goform/goform_set_cmd_process",
            data=data,
            headers=self._headers(),
            timeout=self.timeout,
            verify=False,
        )

    def _compute_ad(self, cr: str, wa: str, rd: str) -> list[str]:
        """Return AD candidates (MC888 uses md5(cr+wa)+rd; others use sha256(wa+cr)+rd)."""
        ads = [
            _md5_upper(_md5_lower(cr + wa) + rd),  # MC888 / ioBroker
            _md5_upper(_md5_lower(wa + cr) + rd),
            _sha256_upper(_sha256_upper(wa + cr) + rd),  # zakmorris MC888 blog
            _sha256_upper(_sha256_upper(cr + wa) + rd),
        ]
        # unique keep order
        out: list[str] = []
        for a in ads:
            if a not in out:
                out.append(a)
        return out

    def logout(self) -> None:
        try:
            payload: dict[str, str] = {"isTest": "false", "goformId": "LOGOUT"}
            if self._ad:
                payload["AD"] = self._ad
            self._post(payload)
        except requests.RequestException:
            pass
        self._cookie = None
        self.session.cookies.clear()
        log.debug("LOGOUT gesendet / Session geleert")

    def login(self) -> str:
        self.session.get(f"{self.base}index.html", timeout=self.timeout, verify=False)

        info = self._get_json(
            {
                "isTest": "false",
                "cmd": "wa_inner_version,cr_version,LD,RD",
                "multi_data": "1",
            }
        )
        wa = str(info.get("wa_inner_version") or self._get_field("wa_inner_version"))
        cr = str(info.get("cr_version") or self._get_field("cr_version"))
        ld = str(info.get("LD") or self._get_field("LD"))
        rd = str(info.get("RD") or self._get_field("RD"))

        is_mc888 = "MC888" in wa.upper() or "MC889" in wa.upper()
        log.info("Router: %s", wa)
        log.debug("LD=%s... RD=%s... cr=%s", ld[:8] if ld else "", rd[:8] if rd else "", cr[:20] if cr else "")

        # Fremde Web-UI-Session stoert MC888 (nur 1 Login) — vorher ausloggen
        self.logout()
        self.session.get(f"{self.base}index.html", timeout=self.timeout, verify=False)
        # LD/RD koennen nach Logout neu sein
        ld = self._get_field("LD") or ld
        rd = self._get_field("RD") or rd
        cr = self._get_field("cr_version") or cr
        wa = self._get_field("wa_inner_version") or wa

        hashed_pw = _sha256_upper(_sha256_upper(self.password) + ld)
        ads = self._compute_ad(cr, wa, rd)
        users = []
        if self.username:
            users.append(self.username)
        # MC888 erwartet oft user=admin, auch wenn die Web-UI keinen Namen zeigt
        for u in ("admin", ""):
            if u not in users:
                users.append(u)

        last_result = ""
        last_body = ""

        for user in users:
            for ad in ads:
                payloads: list[dict[str, str]] = []
                if is_mc888 or True:
                    # Primär: LOGIN_MULTI_USER mit AD (MC888)
                    p_multi: dict[str, str] = {
                        "isTest": "false",
                        "goformId": "LOGIN_MULTI_USER",
                        "password": hashed_pw,
                        "AD": ad,
                    }
                    if user:
                        p_multi["user"] = user
                        p_multi["username"] = user
                    payloads.append(p_multi)

                p_login: dict[str, str] = {
                    "isTest": "false",
                    "goformId": "LOGIN",
                    "password": hashed_pw,
                }
                if user:
                    p_login["user"] = user
                payloads.append(p_login)

                # LOGIN with AD
                p_login_ad = dict(p_login)
                p_login_ad["AD"] = ad
                payloads.append(p_login_ad)

                for payload in payloads:
                    r = self._post(payload)
                    last_body = (r.text or "")[:300]
                    try:
                        data = r.json()
                    except Exception:
                        data = {}
                    last_result = str(data.get("result", ""))
                    stok = self._capture_stok(r)

                    log.debug(
                        "Login user=%r goformId=%s result=%s stok=%s",
                        user or "(leer)",
                        payload.get("goformId"),
                        last_result,
                        "yes" if stok else "no",
                    )

                    if last_result == "3":
                        log.warning(
                            "Router meldet result=3 (andere Session aktiv). "
                            "Bitte Router-Webseite im Browser SCHLIESSEN/ausloggen, dann nochmal."
                        )
                        self.logout()
                        continue

                    if last_result == "1":
                        break  # wrong password for this user — try next user

                    if last_result == "0" or stok:
                        if not stok:
                            # Manchmal kommt stok im naechsten Request
                            self._set_cookie(None)
                            self.session.get(
                                f"{self.base}index.html",
                                headers=self._headers(),
                                timeout=self.timeout,
                                verify=False,
                            )
                            stok = self.session.cookies.get("stok")
                            if stok:
                                stok = str(stok).strip().strip('"')

                        if not stok and last_result != "0":
                            continue

                        self._set_cookie(stok)
                        self._ad = ad
                        # Extra AD variants for later SMS
                        self._ad_list = ads
                        log.info("ZTE-Login OK (stok=%s)", "ja" if stok else "nein")
                        return self._cookie or ""

        raise RuntimeError(
            f"ZTE-Login fehlgeschlagen (result={last_result or '?'}). Antwort: {last_body}. "
            "1) Router-Webseite im Browser komplett schliessen. "
            "2) Passwort in .env pruefen. "
            "3) Bei MC888 oft ZTE_USER=admin setzen."
        )

    def send_sms(self, number: str, message: str, cookie: str | None = None) -> dict[str, Any]:
        if self._ad is None or self._cookie is None:
            self.login()
        assert self._ad is not None

        now = datetime.now().astimezone()
        offset_h = int(now.utcoffset().total_seconds() // 3600) if now.utcoffset() else 1
        sms_time = (
            f"{now.year % 100:02d};{now.month:02d};{now.day:02d};"
            f"{now.hour:02d};{now.minute:02d};{now.second:02d};+{abs(offset_h)}"
        )
        # Also try +0 like some firmwares
        times = [sms_time, sms_time.rsplit(";", 1)[0] + ";+0"]

        body_unicode = message.encode("utf-16-be").hex().upper()
        # GSM7-ish simple hex for ASCII (EXTRA)
        body_gsm = "".join(f"{ord(c):02X}" for c in message)

        ad_list = getattr(self, "_ad_list", [self._ad])
        last: dict[str, Any] = {}

        for ad in ad_list:
            for t in times:
                for encode_type, body in (
                    ("UNICODE", body_unicode),
                    ("GSM7_default", body_gsm),
                ):
                    variants = [
                        {
                            "isTest": "false",
                            "goformId": "SEND_SMS",
                            "Number": number,
                            "sms_time": t,
                            "MessageBody": body,
                            "encode_type": encode_type,
                            "AD": ad,
                        },
                        {
                            "isTest": "false",
                            "goformId": "SEND_SMS",
                            "notCallback": "true",
                            "Number": number,
                            "sms_time": t,
                            "MessageBody": body,
                            "ID": "-1",
                            "encode_type": encode_type,
                            "AD": ad,
                        },
                    ]
                    for data in variants:
                        r = self._post(data)
                        try:
                            last = r.json()
                        except Exception:
                            last = {"raw": r.text, "status_code": r.status_code}
                        log.debug("SEND_SMS try encode=%s -> %s", encode_type, last)
                        result = str(last.get("result", "")).lower()
                        if result in ("success", "0", "ok"):
                            return last
                        if result not in ("failure", "fail", "-1", "error"):
                            # unknown but not hard failure
                            if "success" in str(last).lower():
                                return last

        return last or {"result": "failure"}

    def list_sms(self, cookie: str | None = None, mem_store: int = 1) -> list[dict[str, Any]]:
        if self._ad is None:
            self.login()

        r = self.session.get(
            f"{self.base}goform/goform_get_cmd_process",
            params={
                "isTest": "false",
                "cmd": "sms_data_info",
                "page": "0",
                "data_per_page": "50",
                "mem_store": str(mem_store),
                "tags": "12",
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
        return list(messages)
