"""Pure-mapping tests for whatsapp.client.

The client doesn't touch frappe — we exercise it directly with an httpx
MockTransport so we can assert the outbound JSON payload Meta would see.
"""

from __future__ import annotations

import json

import httpx
import pytest

from lcs_integrations.whatsapp.client import (
    WhatsAppClient,
    WhatsAppClientError,
    _normalize_phone,
)


def test_normalize_phone_strips_separators_and_plus():
    assert _normalize_phone("+49 (170) 123-4567") == "491701234567"
    assert _normalize_phone("0170-123 4567") == "01701234567"


def test_client_rejects_missing_credentials():
    with pytest.raises(WhatsAppClientError):
        WhatsAppClient(access_token="", phone_number_id="123")
    with pytest.raises(WhatsAppClientError):
        WhatsAppClient(access_token="t", phone_number_id="")


def _make_client(handler):
    transport = httpx.MockTransport(handler)
    return WhatsAppClient(access_token="dummy", phone_number_id="42", transport=transport)


def test_send_text_emits_correct_meta_payload():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        captured["auth"] = request.headers.get("Authorization")
        return httpx.Response(200, json={"messages": [{"id": "wamid.ABC123"}]})

    client = _make_client(handler)
    try:
        result = client.send_text(to="+49 170 1234567", body="Hallo, Welt")
    finally:
        client.close()

    assert result["messages"][0]["id"] == "wamid.ABC123"
    assert "/42/messages" in captured["url"]
    assert captured["auth"] == "Bearer dummy"
    body = captured["body"]
    assert body["messaging_product"] == "whatsapp"
    assert body["to"] == "491701234567"
    assert body["type"] == "text"
    assert body["text"]["body"] == "Hallo, Welt"
    assert body["text"]["preview_url"] is False


def test_send_template_includes_language_and_components():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"messages": [{"id": "wamid.T1"}]})

    client = _make_client(handler)
    try:
        client.send_template(
            to="491701234567",
            template_name="welcome_lcs",
            language="de",
            components=[{"type": "body", "parameters": [{"type": "text", "text": "Erika"}]}],
        )
    finally:
        client.close()

    body = captured["body"]
    assert body["type"] == "template"
    assert body["template"]["name"] == "welcome_lcs"
    assert body["template"]["language"]["code"] == "de"
    assert body["template"]["components"][0]["parameters"][0]["text"] == "Erika"


def test_send_text_raises_on_4xx():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "invalid token"}})

    client = _make_client(handler)
    try:
        with pytest.raises(WhatsAppClientError) as exc_info:
            client.send_text(to="491701234567", body="x")
    finally:
        client.close()
    assert "Meta HTTP 401" in str(exc_info.value)
