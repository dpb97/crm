"""HMAC signing / verification tests for the abas client.

Focus on the security-critical surface: `verify_inbound` must reject replayed
requests (stale timestamps) and tampered payloads; the outbound signer must
produce a deterministic signature given the same secret + timestamp + body.
"""

from __future__ import annotations

import hmac
import os
import time
from hashlib import sha256

import httpx
import pytest


@pytest.fixture
def client_module(monkeypatch: pytest.MonkeyPatch):
    """Import the abas client fresh per test — it reads env vars at init time."""
    monkeypatch.setenv("ABAS_BASE_URL", "https://abas.test.invalid")
    monkeypatch.setenv("ABAS_HMAC_KEY", "unit-test-key")
    import importlib

    module = importlib.import_module("lcs_integrations.abas.client")
    return importlib.reload(module)


# --- verify_inbound (inbound HMAC check) ------------------------------------


def _make_signature(body: bytes, ts: str, key: bytes) -> str:
    # Must mirror client._sign / verify_inbound exactly — "ts\nbody".
    return hmac.new(key, ts.encode() + b"\n" + body, sha256).hexdigest()


def test_verify_inbound_accepts_valid_signature(client_module):
    key = b"unit-test-key"
    body = b'{"event":"shipment"}'
    ts = str(int(time.time()))
    sig = _make_signature(body, ts, key)

    assert client_module.AbasClient.verify_inbound(body=body, ts=ts, signature=sig, key=key)


def test_verify_inbound_rejects_wrong_signature(client_module):
    body = b'{"event":"shipment"}'
    ts = str(int(time.time()))

    assert not client_module.AbasClient.verify_inbound(
        body=body, ts=ts, signature="deadbeef", key=b"unit-test-key"
    )


def test_verify_inbound_rejects_tampered_body(client_module):
    key = b"unit-test-key"
    body = b'{"event":"shipment"}'
    ts = str(int(time.time()))
    sig = _make_signature(body, ts, key)

    tampered = b'{"event":"CANCEL"}'
    assert not client_module.AbasClient.verify_inbound(
        body=tampered, ts=ts, signature=sig, key=key
    )


def test_verify_inbound_rejects_stale_timestamp(client_module):
    key = b"unit-test-key"
    body = b'{"event":"shipment"}'
    stale_ts = str(int(time.time()) - 600)  # 10 min old > 300 s window
    sig = _make_signature(body, stale_ts, key)

    assert not client_module.AbasClient.verify_inbound(
        body=body, ts=stale_ts, signature=sig, key=key
    )


def test_verify_inbound_rejects_non_numeric_timestamp(client_module):
    assert not client_module.AbasClient.verify_inbound(
        body=b"{}", ts="not-a-number", signature="irrelevant", key=b"k"
    )


# --- _sign (outbound HMAC) --------------------------------------------------


def test_sign_produces_matching_signature(client_module):
    client = client_module.AbasClient(transport=httpx.MockTransport(lambda _r: httpx.Response(200)))
    try:
        headers = client._sign("POST", "/api/customers", b'{"a":1}')
    finally:
        client.close()

    assert "X-LCS-Timestamp" in headers
    assert "X-LCS-Signature" in headers
    # The signature must match a locally recomputed HMAC over
    # method\npath\nts\nbody with the same key.
    ts = headers["X-LCS-Timestamp"]
    expected = hmac.new(
        os.environ["ABAS_HMAC_KEY"].encode(),
        b"POST\n/api/customers\n" + ts.encode() + b"\n" + b'{"a":1}',
        sha256,
    ).hexdigest()
    assert headers["X-LCS-Signature"] == expected
