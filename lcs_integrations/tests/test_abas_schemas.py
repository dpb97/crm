"""Pydantic validation round-trip for the abas DTOs.

These are fast and cheap; they mainly guard against accidental schema drift
between the abas contract and our Python models.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from lcs_integrations.abas.schemas import (
    AbasContact,
    AbasCustomer,
    AbasOrderHeader,
    AbasQuotationHeader,
    DeliveryStatusEvent,
)


def test_customer_accepts_minimal_payload():
    c = AbasCustomer(abas_id="K12345", name="Acme AG")
    assert c.abas_id == "K12345"
    assert c.name == "Acme AG"


def test_customer_rejects_empty_id():
    with pytest.raises(ValidationError):
        AbasCustomer(abas_id="", name="Acme AG")


def test_customer_rejects_empty_name():
    with pytest.raises(ValidationError):
        AbasCustomer(abas_id="K1", name="")


def test_customer_strips_whitespace():
    c = AbasCustomer(abas_id="  K12345  ", name="  Acme AG  ")
    # extra="ignore" + str_strip_whitespace — whitespace must be stripped.
    assert c.abas_id == "K12345"
    assert c.name == "Acme AG"


def test_customer_ignores_unknown_fields():
    # extra="ignore" — drift should not break parsing.
    c = AbasCustomer(abas_id="K1", name="Acme", some_new_field="x")  # type: ignore[call-arg]
    assert "some_new_field" not in c.model_dump()


def test_contact_requires_last_name_and_customer_id():
    with pytest.raises(ValidationError):
        AbasContact(abas_id="C-9001", customer_abas_id="K1")  # type: ignore[call-arg]


def test_contact_round_trip():
    c = AbasContact(
        abas_id="C-9001",
        customer_abas_id="K12345",
        first_name="Jane",
        last_name="Doe",
        email="j.doe@example.com",
    )
    data = c.model_dump()
    assert data["email"] == "j.doe@example.com"
    assert data["customer_abas_id"] == "K12345"


def test_quotation_requires_customer_and_total():
    with pytest.raises(ValidationError):
        AbasQuotationHeader(abas_id="A-1", quotation_no="Q-1", created_on=date(2026, 4, 16), total=100.0)  # type: ignore[call-arg]


def test_order_header_defaults_to_open_status():
    o = AbasOrderHeader(
        abas_id="O-1",
        customer_abas_id="K12345",
        order_no="20260416-1",
        created_on=date(2026, 4, 16),
        total=1234.5,
    )
    assert o.status == "open"


def test_order_header_rejects_unknown_status():
    with pytest.raises(ValidationError):
        AbasOrderHeader(
            abas_id="O-1",
            customer_abas_id="K1",
            order_no="X",
            created_on=date(2026, 4, 16),
            total=1.0,
            status="invented",  # type: ignore[arg-type]
        )


def test_delivery_status_event_accepts_capitalised_literal():
    ev = DeliveryStatusEvent(
        order_no="20260416-1",
        status="Shipped",
        planned_ship_date=date(2026, 5, 1),
        shipped_at=datetime(2026, 4, 16, 10, 0, tzinfo=timezone.utc),
    )
    assert ev.status == "Shipped"


def test_delivery_status_event_rejects_lowercase_literal():
    with pytest.raises(ValidationError):
        DeliveryStatusEvent(order_no="20260416-1", status="shipped")  # type: ignore[arg-type]
