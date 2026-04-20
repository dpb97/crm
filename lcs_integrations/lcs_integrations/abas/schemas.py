"""Pydantic DTOs for the abas ERP integration.

Kept deliberately narrow — only the fields negotiated in the LCS minimum
feature set (customer master, quotation header, order header, delivery
status). The surface can grow later without breaking consumers thanks to
`extra="ignore"`.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _BaseDTO(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)


class AbasCustomer(_BaseDTO):
    abas_id: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1)
    email: str | None = None
    phone: str | None = None
    country: str | None = None
    vat_id: str | None = None


class AbasContact(_BaseDTO):
    abas_id: str
    customer_abas_id: str
    first_name: str | None = None
    last_name: str
    email: str | None = None
    phone: str | None = None


class AbasQuotationHeader(_BaseDTO):
    abas_id: str
    customer_abas_id: str
    quotation_no: str
    created_on: date
    total: float


class AbasOrderHeader(_BaseDTO):
    abas_id: str
    customer_abas_id: str
    order_no: str
    created_on: date
    total: float
    status: Literal["open", "confirmed", "shipped", "delivered"] = "open"


class DeliveryStatusEvent(_BaseDTO):
    order_no: str
    status: Literal["Pending", "Planned", "Shipped", "Delivered"]
    planned_ship_date: date | None = None
    shipped_at: datetime | None = None
