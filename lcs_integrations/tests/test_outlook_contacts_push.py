"""Push-side mapping tests for outlook_sync.contacts_push.

The push module is `frappe`-coupled; we exercise the pure mapping helper
`_to_graph_payload` only. Service-level orchestration (HTTP, hooks) is
covered by integration tests against a real bench.
"""

from __future__ import annotations

import types

import pytest


@pytest.fixture
def push_module(frappe_stub):
    # Import lazily so the frappe stub is in place
    from lcs_integrations.outlook_sync import contacts_push

    return contacts_push


def _contact(**kwargs):
    """Minimal stand-in mimicking frappe.model.document.Document.get()."""
    base = {
        "first_name": "Erika",
        "last_name": "Mustermann",
        "full_name": "Erika Mustermann",
        "company_name": "ACME GmbH",
        "designation": "CTO",
        "email_ids": [],
        "phone_nos": [],
    }
    base.update(kwargs)
    obj = types.SimpleNamespace(**base)
    obj.get = lambda key: base.get(key, [])
    return obj


def test_to_graph_payload_basic_fields(push_module):
    contact = _contact()
    payload = push_module._to_graph_payload(contact)
    assert payload["givenName"] == "Erika"
    assert payload["surname"] == "Mustermann"
    assert payload["displayName"] == "Erika Mustermann"
    assert payload["companyName"] == "ACME GmbH"
    assert payload["jobTitle"] == "CTO"


def test_to_graph_payload_emails_and_phones(push_module):
    contact = _contact(
        email_ids=[
            types.SimpleNamespace(email_id="erika@example.com"),
            types.SimpleNamespace(email_id="erika.private@example.org"),
        ],
        phone_nos=[
            types.SimpleNamespace(phone="+49 89 1234", get=lambda k: 0),
            types.SimpleNamespace(phone="+49 170 9999", get=lambda k: 1 if k == "is_primary_mobile_no" else 0),
        ],
    )
    contact.get = lambda key: getattr(contact, key, [])

    payload = push_module._to_graph_payload(contact)
    addrs = [e["address"] for e in payload["emailAddresses"]]
    assert addrs == ["erika@example.com", "erika.private@example.org"]
    assert payload["businessPhones"] == ["+49 89 1234"]
    assert payload["mobilePhone"] == "+49 170 9999"


def test_to_graph_payload_skips_empty_collections(push_module):
    contact = _contact(email_ids=[], phone_nos=[])
    payload = push_module._to_graph_payload(contact)
    assert "emailAddresses" not in payload
    assert "businessPhones" not in payload
    assert "mobilePhone" not in payload
