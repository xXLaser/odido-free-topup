"""Minimal ZTE consumer-router client (MC801/MC888-style goform API)."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from typing import Any

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

log = logging.getLogger("zte")


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest().upper()


def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


class ZteRouter:
    def __init__(
        self,
        host: str,
        password: str,
        username: str | None = "admin",
        timeout: float = 15.0,
    ) -> None:
        self.host = host.strip().removeprefix("http://").removeprefix("https://").rstrip("/")
        self.password = password
        self.username = username or ""
        self.timeout = timeout
        self.session = requests.Session()
        self.base = f"http://{self.host}/"
        self._ad: str | None = None
        self._probe_https()

    def _probe_https(self) -> None:
        for scheme in ("http", "https"):
            try:
                r = self.session.get(f"{scheme}://{self.host}/", timeout=5, verify=False)
                if r.ok or r.status_code in (401, 403):
                    self.base = f"{scheme}://{self.host}/"
                    return
            except requests.RequestException:
                continue

    def _headers(self, cookie: str | None = None) -> dict[str, str]:
        h = {
            "Referer": f"{self.base}index.html",
            "X-Requested-With": "XMLHttpRequest",
        }
        if cookie:
            h["Cookie"] = cookie
        return h

    def _get_json(self, params: dict[str, str], cookie: str | None = None) -> dict[str, Any]:
        r = self.session.get(
            f"{self.base}goform/goform_get_cmd_process",
            params=params,
            headers=self._headers(cookie),
            timeout=self.timeout,
            verify=False,
        )
        r.raise_for_status()
        return r.json()

    def _post(self, data: dict[str, str], cookie: str | None = None) -> requests.Response:
        return self.session.post(
            f"{self.base}goform/goform_set_cmd_process",
            data=data,
            headers=self._headers(cookie),
            timeout=self.timeout,
            verify=False,
        )

    def login(self) -> str:
        info = self._get_json(
            {
                "isTest": "false",
                "cmd": "wa_inner_version,cr_version,LD,RD",
                "multi_data": "1",
            }
        )
        ld = str(info.get("LD", "")).upper()
        if not ld:
            ld = str(self._get_json({"isTest": "false", "cmd": "LD"}).get("LD", "")).upper()

        hashed = _sha256(_sha256(self.password) + ld)
        version = str(info.get("wa_inner_version", ""))
        use_multi = "MC801" not in version and "MC7010" not in version

        payload: dict[str, str] = {
            "isTest": "false",
            "goformId": "LOGIN_MULTI_USER" if use_multi and self.username else "LOGIN",
            "password": hashed,
        }
        if self.username:
            payload["username"] = self.username
            # Some firmwares use "user" instead of username
            payload["user"] = self.username

        r = self._post(payload)
        r.raise_for_status()
        stok = r.cookies.get("stok")
        if not stok:
            # Retry simpler LOGIN (password-only devices)
            r = self._post(
                {
                    "isTest": "false",
                    "goformId": "LOGIN",
                    "password": hashed,
                }
            )
            r.raise_for_status()
            stok = r.cookies.get("stok")
        if not stok:
            body = (r.text or "")[:200]
            raise RuntimeError(f"ZTE-Login fehlgeschlagen (kein stok). Antwort: {body}")

        cookie = f"stok={stok.strip(chr(34))}"
        wa = str(info.get("wa_inner_version") or "")
        cr = str(info.get("cr_version") or "")
        rd = str(info.get("RD") or "")
        if not rd:
            rd = str(self._get_json({"isTest": "false", "cmd": "RD"}, cookie).get("RD", ""))

        use_sha = any(x in wa.upper() for x in ("MC888", "MC889", "MC801A"))
        h = _sha256 if use_sha else _md5
        # Newer firmwares often want SHA256 even when model string differs
        try:
            self._ad = _sha256(_sha256(wa + cr) + rd)
        except Exception:
            self._ad = h(h(wa + cr) + rd)

        log.info("ZTE-Login OK (%s)", self.host)
        return cookie

    def send_sms(self, number: str, message: str, cookie: str | None = None) -> dict[str, Any]:
        if cookie is None or self._ad is None:
            cookie = self.login()
        assert self._ad is not None

        now = datetime.now().astimezone()
        offset_h = int(now.utcoffset().total_seconds() // 3600) if now.utcoffset() else 1
        sms_time = (
            f"{now.year % 100:02d};{now.month:02d};{now.day:02d};"
            f"{now.hour:02d};{now.minute:02d};{now.second:02d};"
            f"{offset_h:+d}".replace("+", "+")
        )
        # ZTE expects +N without zero-pad issues; keep simple +1/+2
        sms_time = (
            f"{now.year % 100:02d};{now.month:02d};{now.day:02d};"
            f"{now.hour:02d};{now.minute:02d};{now.second:02d};+{abs(offset_h)}"
        )

        body_hex = message.encode("utf-16-be").hex().upper()
        data = {
            "isTest": "false",
            "goformId": "SEND_SMS",
            "notCallback": "true",
            "Number": number,
            "sms_time": sms_time,
            "MessageBody": body_hex,
            "ID": "-1",
            "encode_type": "UNICODE",
            "AD": self._ad,
        }
        r = self._post(data, cookie)
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return {"raw": r.text, "status_code": r.status_code}

    def list_sms(self, cookie: str | None = None, mem_store: int = 1) -> list[dict[str, Any]]:
        """Read SMS inbox (mem_store=1 typically = SIM/device inbox)."""
        if cookie is None or self._ad is None:
            cookie = self.login()

        # Common endpoint used by ZTE web UI
        r = self.session.get(
            f"{self.base}goform/goform_get_cmd_process",
            params={
                "isTest": "false",
                "cmd": "sms_data_info",
                "page": "0",
                "data_per_page": "50",
                "mem_store": str(mem_store),
                "tags": "12",
                "order_by": "order+by+id+desc",
            },
            headers=self._headers(cookie),
            timeout=self.timeout,
            verify=False,
        )
        r.raise_for_status()
        data = r.json()
        messages = data.get("messages") or data.get("Messages") or []
        if isinstance(messages, dict):
            messages = list(messages.values())
        return list(messages)

    def delete_sms(self, sms_id: str, cookie: str | None = None) -> None:
        if cookie is None or self._ad is None:
            cookie = self.login()
        assert self._ad is not None
        self._post(
            {
                "isTest": "false",
                "goformId": "DELETE_SMS",
                "msg_id": str(sms_id),
                "AD": self._ad,
            },
            cookie,
        )
