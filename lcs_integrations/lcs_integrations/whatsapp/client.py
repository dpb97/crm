"""Meta Cloud API client for WhatsApp Business.

Thin HTTP wrapper — same shape as outlook_sync.GraphClient. Settings come
from `LCS WhatsApp Settings` so credentials never live in env / files.
"""

from __future__ import annotations

from typing import Any

import httpx


META_GRAPH_VERSION = "v19.0"
META_GRAPH_BASE = f"https://graph.facebook.com/{META_GRAPH_VERSION}"


class WhatsAppClientError(RuntimeError):
    pass


class WhatsAppClient:
    def __init__(
        self,
        *,
        access_token: str,
        phone_number_id: str,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not access_token or not phone_number_id:
            raise WhatsAppClientError("WhatsApp client requires access_token and phone_number_id")
        self._token = access_token
        self._phone_number_id = phone_number_id
        self._http = httpx.Client(
            base_url=META_GRAPH_BASE,
            transport=transport,
            timeout=httpx.Timeout(connect=5.0, read=30.0, write=30.0, pool=5.0),
        )

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}

    def _check(self, resp: httpx.Response) -> dict[str, Any]:
        if resp.status_code >= 400:
            raise WhatsAppClientError(f"Meta HTTP {resp.status_code}: {resp.text[:500]}")
        return resp.json() if resp.content else {}

    def send_text(self, *, to: str, body: str) -> dict[str, Any]:
        """Send a free-form text message.

        Note: free-form replies are only allowed within the 24-hour customer-
        service window. For new outreach, use `send_template` instead.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": _normalize_phone(to),
            "type": "text",
            "text": {"preview_url": False, "body": body},
        }
        resp = self._http.post(
            f"/{self._phone_number_id}/messages",
            json=payload,
            headers=self._headers(),
        )
        return self._check(resp)

    def send_template(
        self,
        *,
        to: str,
        template_name: str,
        language: str = "de",
        components: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": _normalize_phone(to),
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
            },
        }
        if components:
            payload["template"]["components"] = components
        resp = self._http.post(
            f"/{self._phone_number_id}/messages",
            json=payload,
            headers=self._headers(),
        )
        return self._check(resp)

    def close(self) -> None:
        self._http.close()


def _normalize_phone(raw: str) -> str:
    """Meta requires E.164 without leading '+' — normalise both formats."""
    cleaned = "".join(ch for ch in (raw or "") if ch.isdigit() or ch == "+")
    return cleaned.lstrip("+")
