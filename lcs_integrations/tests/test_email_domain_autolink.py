"""Tests for the email-domain auto-link helper.

Pure-logic tests — the full `auto_link` function touches the DB and lives
under the `integration` marker. Here we cover the domain-parsing helper and
the personal-domain deny list (both now owned by `contacts.domain_binding`,
the canonical resolver) plus `auto_link`'s early-exit guards.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def binding(frappe_stub):  # noqa: ARG001 — fixture installs the stub
    mod = importlib.import_module("lcs_integrations.contacts.domain_binding")
    return importlib.reload(mod)


@pytest.fixture
def module(frappe_stub):  # noqa: ARG001 — fixture installs the stub
    mod = importlib.import_module("lcs_integrations.email_domain_autolink.hooks")
    return importlib.reload(mod)


@pytest.mark.parametrize(
    ("email", "expected"),
    [
        ("jane.doe@acme.com", "acme.com"),
        ("a@b.c", "b.c"),
        ("MIXED@CORP.AT", "corp.at"),
        ("no-at-sign", None),
        ("", None),
        (None, None),
    ],
)
def test_domain_extraction(binding, email, expected):
    assert binding.domain_of(email) == expected


@pytest.mark.parametrize(
    "personal",
    ["gmail.com", "gmx.at", "gmx.de", "outlook.com", "hotmail.com", "yahoo.com", "icloud.com"],
)
def test_personal_domains_are_denied(binding, personal):
    assert personal in binding.PERSONAL_DOMAINS
    assert binding.is_bindable_domain(personal) is False


@pytest.mark.parametrize(
    "corporate",
    ["acme.com", "lcs.at", "customer.de", "lcs-cable-cranes.com"],
)
def test_corporate_domains_pass(binding, corporate):
    assert corporate not in binding.PERSONAL_DOMAINS
    assert binding.is_bindable_domain(corporate) is True


def test_auto_link_skips_non_email_communication(module, monkeypatch):
    """Non-email Communications (e.g. Chat) must not touch the DB."""
    calls = {"sql": 0}

    def _spy(*_args, **_kwargs):
        calls["sql"] += 1
        return []

    monkeypatch.setattr(module.frappe.db, "sql", _spy, raising=False)

    class _Doc:
        reference_doctype = None
        sender = "x@acme.com"

        def get(self, key, default=None):
            return {"communication_medium": "Chat"}.get(key, default)

    module.auto_link(_Doc())
    assert calls["sql"] == 0


def test_auto_link_skips_already_linked(module, monkeypatch):
    calls = {"sql": 0}
    monkeypatch.setattr(
        module.frappe.db,
        "sql",
        lambda *a, **k: (calls.__setitem__("sql", calls["sql"] + 1), [])[1],
        raising=False,
    )

    class _Doc:
        reference_doctype = "CRM Deal"
        sender = "x@acme.com"

        def get(self, key, default=None):
            return {"communication_medium": "Email"}.get(key, default)

    module.auto_link(_Doc())
    assert calls["sql"] == 0


def test_auto_link_skips_personal_domain(module, monkeypatch):
    """Personal-domain mail resolves to no bindable domain — no org lookup."""
    seen = {"org_for_domain": 0}
    monkeypatch.setattr(
        module,
        "org_for_domain",
        lambda *_a, **_k: seen.__setitem__("org_for_domain", seen["org_for_domain"] + 1),
        raising=False,
    )

    class _Doc:
        reference_doctype = None
        sender = "user@gmail.com"

        def get(self, key, default=None):
            return {"communication_medium": "Email"}.get(key, default)

    module.auto_link(_Doc())
    assert seen["org_for_domain"] == 0
