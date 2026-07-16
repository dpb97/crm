"""HTTP client for the Proxess DMS REST API.

Proxess credentials are per-user (OAuth2 client_credentials flow against the
Proxess AD integration). The client caches tokens in-memory for the TTL
returned by the server.
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class ProxessClientError(RuntimeError):
    def __init__(self, status: int, body: str) -> None:
        super().__init__(f"Proxess returned HTTP {status}: {body[:500]}")
        self.status = status


class ProxessClient:
    def __init__(self, *, transport: httpx.BaseTransport | None = None) -> None:
        self._base = os.environ["PROXESS_BASE_URL"].rstrip("/")
        self._client_id = os.environ["PROXESS_CLIENT_ID"]
        self._client_secret = os.environ["PROXESS_CLIENT_SECRET"]
        self._http = httpx.Client(base_url=self._base, transport=transport,
                                  timeout=httpx.Timeout(connect=5.0, read=60.0, write=60.0, pool=5.0))
        self._token: str | None = None
        self._token_exp: float = 0.0

    def _token_valid(self) -> str:
        if self._token and self._token_exp > time.time() + 30:
            return self._token
        resp = self._http.post("/oauth/token", data={
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        })
        if resp.status_code >= 400:
            raise ProxessClientError(resp.status_code, resp.text)
        body = resp.json()
        self._token = body["access_token"]
        self._token_exp = time.time() + int(body.get("expires_in", 3600))
        return self._token

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=8),
        retry=retry_if_exception_type((httpx.TransportError, httpx.ReadTimeout)),
    )
    def upload(self, title: str, content_type: str, data: bytes, *, meta: dict[str, Any]) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self._token_valid()}"}
        files = {"file": (title, data, content_type)}
        resp = self._http.post("/api/documents", headers=headers, files=files, data={"meta": meta})
        if resp.status_code >= 400:
            raise ProxessClientError(resp.status_code, resp.text)
        return resp.json()

    def list_for(self, reference_doctype: str, reference_name: str) -> list[dict[str, Any]]:
        headers = {"Authorization": f"Bearer {self._token_valid()}"}
        resp = self._http.get("/api/documents", params={
            "meta.ref_doctype": reference_doctype,
            "meta.ref_name": reference_name,
        }, headers=headers)
        if resp.status_code >= 400:
            raise ProxessClientError(resp.status_code, resp.text)
        return resp.json().get("items", [])

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "ProxessClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
