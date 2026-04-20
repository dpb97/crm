"""HTTP client for the abas ERP REST bridge.

Network concerns only. No Frappe imports here, so the client is unit-testable
against `httpx.MockTransport`. Business logic lives in `service.py`.
"""

from __future__ import annotations

import hmac
import os
import time
from hashlib import sha256
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


_DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=30.0, pool=5.0)


class AbasClientError(RuntimeError):
    def __init__(self, status: int, body: str) -> None:
        super().__init__(f"abas returned HTTP {status}: {body[:500]}")
        self.status = status
        self.body = body


class AbasClient:
    """Thin, retry-aware wrapper around the abas REST bridge.

    Credentials are read from environment variables (injected from Key Vault in
    production, `.env` in development). Never pass them in the constructor
    from Frappe controllers — that would leak secrets into serialized logs.
    """

    def __init__(self, *, transport: httpx.BaseTransport | None = None) -> None:
        self._base_url = os.environ["ABAS_BASE_URL"].rstrip("/")
        self._hmac_key = os.environ["ABAS_HMAC_KEY"].encode()
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=_DEFAULT_TIMEOUT,
            transport=transport,
        )

    # ---- Signing ----
    def _sign(self, method: str, path: str, body: bytes) -> dict[str, str]:
        ts = str(int(time.time()))
        to_sign = b"\n".join([method.encode(), path.encode(), ts.encode(), body])
        digest = hmac.new(self._hmac_key, to_sign, sha256).hexdigest()
        return {"X-LCS-Timestamp": ts, "X-LCS-Signature": digest}

    @staticmethod
    def verify_inbound(body: bytes, ts: str, signature: str, key: bytes, *, max_skew: int = 300) -> bool:
        try:
            ts_int = int(ts)
        except ValueError:
            return False
        if abs(time.time() - ts_int) > max_skew:
            return False
        expected = hmac.new(key, ts.encode() + b"\n" + body, sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    # ---- HTTP ----
    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((httpx.TransportError, httpx.ReadTimeout)),
    )
    def _request(self, method: str, path: str, *, json: Any = None) -> dict[str, Any]:
        body = b"" if json is None else httpx._content.encode_json(json)  # type: ignore[attr-defined]
        headers = self._sign(method, path, body)
        headers["Content-Type"] = "application/json"
        response = self._client.request(method, path, content=body, headers=headers)
        if response.status_code >= 400:
            raise AbasClientError(response.status_code, response.text)
        return response.json() if response.content else {}

    # ---- High-level ops ----
    def push_customer(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/customers", json=payload)

    def pull_customer(self, abas_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/customers/{abas_id}")

    def pull_order(self, order_no: str) -> dict[str, Any]:
        return self._request("GET", f"/api/orders/{order_no}")

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "AbasClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
