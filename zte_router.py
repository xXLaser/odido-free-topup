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

# Common LOGIN result codes on ZTE consumer firmware
LOGIN_RESULT_HINTS = {
    "0": "ok (bei vielen Firmwares = Erfolg)",
    "1": "falsches Passwort",
    "2": "unbekannt / gesperrt",
    "3": "bereits eingeloggt",
    "4": "zu viele Versuche",
}


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest().upper()


def _md5(s: str) -> str:
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
        self._probe_https()

    def _probe_https(self) -> None:
        for scheme in ("http", "https"):
            try:
                r = self.session.get(f"{scheme}://{self.host}/", timeout=5, verify=False)
                if r.ok or r.status_code in (401, 403, 302):
                    self.base = f"{scheme}://{self.host}/"
                    # Warm up session / cookies like a browser
                    self.session.get(f"{self.base}index.html", timeout=5, verify=False)
                    return
            except requests.RequestException:
                continue

    def _headers(self, cookie: str | None = None) -> dict[str, str]:
        h = {
            "Referer": f"{self.base}index.html",
            "Origin": self.base.rstrip("/"),
            "X-Requested-With": "XMLHttpRequest",
        }
        c = cookie or self._cookie
        if c:
            h["Cookie"] = c
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

    def _pick_stok(self, response: requests.Response) -> str | None:
        for jar in (response.cookies, self.session.cookies):
            stok = jar.get("stok")
            if stok:
                return stok.strip().strip('"')
        # Some firmwares put it in the JSON body
        try:
            data = response.json()
            for key in ("stok", "token", "SID"):
                if data.get(key):
                    return str(data[key]).strip().strip('"')
        except Exception:
            pass
        return None

    def _password_variants(self, ld: str) -> list[tuple[str, str]]:
        """Return (label, hashed_password) candidates."""
        pw = self.password
        variants: list[tuple[str, str]] = []
        if ld:
            variants.append(("sha256(sha256(pw)+LD)", _sha256(_sha256(pw) + ld)))
            variants.append(("sha256(sha256(pw)+ld_raw)", _sha256(_sha256(pw) + ld.lower())))
            variants.append(("md5(md5(pw)+LD)", _md5(_md5(pw.lower()) + ld)))
        variants.append(("sha256(pw)", _sha256(pw)))
        variants.append(("plain", pw))
        # de-dupe keeping order
        seen: set[str] = set()
        out: list[tuple[str, str]] = []
        for label, val in variants:
            if val not in seen:
                seen.add(val)
                out.append((label, val))
        return out

    def _login_payloads(self, hashed: str) -> list[dict[str, str]]:
        payloads: list[dict[str, str]] = []

        # Password-only LOGIN (many ZTE home routers — no username field)
        payloads.append({"isTest": "false", "goformId": "LOGIN", "password": hashed})

        if self.username:
            payloads.append(
                {
                    "isTest": "false",
                    "goformId": "LOGIN",
                    "password": hashed,
                    "user": self.username,
                }
            )
            payloads.append(
                {
                    "isTest": "false",
                    "goformId": "LOGIN_MULTI_USER",
                    "password": hashed,
                    "username": self.username,
                }
            )
            payloads.append(
                {
                    "isTest": "false",
                    "goformId": "LOGIN_MULTI_USER",
                    "password": hashed,
                    "user": self.username,
                    "username": self.username,
                }
            )
        else:
            # Still try MULTI_USER with empty user on some firmwares
            payloads.append(
                {
                    "isTest": "false",
                    "goformId": "LOGIN_MULTI_USER",
                    "password": hashed,
                    "username": "",
                }
            )
        return payloads

    def _finish_login(self, stok: str | None, info: dict[str, Any]) -> str:
        cookie = f"stok={stok}" if stok else ""
        # Merge any session cookies into header string
        parts = []
        if stok:
            parts.append(f"stok={stok}")
        for c in self.session.cookies:
            if c.name != "stok":
                parts.append(f"{c.name}={c.value}")
        if parts:
            cookie = "; ".join(parts)
        self._cookie = cookie or None

        wa = str(info.get("wa_inner_version") or "")
        cr = str(info.get("cr_version") or "")
        rd = str(info.get("RD") or "")
        if not rd:
            try:
                rd = str(self._get_json({"isTest": "false", "cmd": "RD"}, cookie).get("RD", ""))
            except Exception:
                rd = ""

        # Prefer SHA256 AD (MC888/modern); also keep md5 fallback stored via try
        self._ad = _sha256(_sha256(wa + cr) + rd) if (wa or cr or rd) else _sha256(rd or "0")
        # Alternate AD used by older models
        self._ad_md5 = _md5(_md5(wa + cr) + rd)

        log.info("ZTE-Login OK (%s) version=%s", self.host, wa or "?")
        return cookie

    def login(self) -> str:
        # Browser-like warm-up
        try:
            self.session.get(f"{self.base}index.html", timeout=self.timeout, verify=False)
        except requests.RequestException:
            pass

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

        log.debug("Router version=%s LD=%s...", info.get("wa_inner_version"), ld[:8] if ld else "")

        last_body = ""
        last_result = ""

        for hash_label, hashed in self._password_variants(ld):
            for payload in self._login_payloads(hashed):
                # Fresh-ish session cookies between attempts help some firmwares
                r = self._post(payload)
                last_body = (r.text or "")[:300]
                try:
                    data = r.json()
                except Exception:
                    data = {}
                last_result = str(data.get("result", ""))
                stok = self._pick_stok(r)

                log.debug(
                    "Login try hash=%s goformId=%s result=%s stok=%s",
                    hash_label,
                    payload.get("goformId"),
                    last_result,
                    "yes" if stok else "no",
                )

                # Success: result 0 / 3, or we got a stok cookie
                if last_result == "1":
                    log.debug("Passwort-Hash %s abgelehnt", hash_label)
                    break

                if stok or last_result in ("0", "3"):
                    if not stok and last_result in ("0", "3"):
                        # Manche Firmwares setzen stok erst beim naechsten Request
                        try:
                            self.session.get(
                                f"{self.base}index.html",
                                headers=self._headers(),
                                timeout=self.timeout,
                                verify=False,
                            )
                            stok = self.session.cookies.get("stok")
                        except requests.RequestException:
                            pass
                    return self._finish_login(stok, info)

        hint = LOGIN_RESULT_HINTS.get(last_result, "unbekannter Code")
        raise RuntimeError(
            f"ZTE-Login fehlgeschlagen (result={last_result or '?'} = {hint}). "
            f"Antwort: {last_body}. "
            "Tipp: ZTE_USER leer lassen (kein Benutzer), Passwort wie in der Router-Webseite pruefen."
        )

    def send_sms(self, number: str, message: str, cookie: str | None = None) -> dict[str, Any]:
        if cookie is None or self._ad is None:
            cookie = self.login()
        assert self._ad is not None

        now = datetime.now().astimezone()
        offset_h = int(now.utcoffset().total_seconds() // 3600) if now.utcoffset() else 1
        sms_time = (
            f"{now.year % 100:02d};{now.month:02d};{now.day:02d};"
            f"{now.hour:02d};{now.minute:02d};{now.second:02d};+{abs(offset_h)}"
        )

        body_hex = message.encode("utf-16-be").hex().upper()

        def _do_send(ad: str) -> requests.Response:
            return self._post(
                {
                    "isTest": "false",
                    "goformId": "SEND_SMS",
                    "notCallback": "true",
                    "Number": number,
                    "sms_time": sms_time,
                    "MessageBody": body_hex,
                    "ID": "-1",
                    "encode_type": "UNICODE",
                    "AD": ad,
                },
                cookie,
            )

        r = _do_send(self._ad)
        # If AD rejected, retry with md5-style AD
        try:
            data = r.json()
            if str(data.get("result")) not in ("success", "0", "") and getattr(self, "_ad_md5", None):
                r = _do_send(self._ad_md5)
                data = r.json()
            return data
        except Exception:
            return {"raw": r.text, "status_code": r.status_code}

    def list_sms(self, cookie: str | None = None, mem_store: int = 1) -> list[dict[str, Any]]:
        if cookie is None or self._ad is None:
            cookie = self.login()

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
