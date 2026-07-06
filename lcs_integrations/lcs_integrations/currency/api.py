"""Whitelisted FX endpoints for the SPA.

`get_live_rate` is the workhorse — the offer detail page calls it on
mount and on every currency/value change to render the side-by-side
"frozen vs. live" panel.
"""

from __future__ import annotations

import frappe

from .frankfurter import get_rate, convert


@frappe.whitelist()
def get_live_rate(from_ccy: str, to_ccy: str = "EUR") -> dict:
    """Return the latest published rate plus a convert helper result.

    Output:
      {"from": "USD", "to": "EUR", "rate": 0.92, "source": "frankfurter.dev"}

    `rate` is None if the upstream API failed (e.g. no internet) — the
    SPA renders an "rate unavailable" hint in that case rather than a
    misleading conversion.
    """
    rate = get_rate(from_ccy, to_ccy)
    return {
        "from": (from_ccy or "").upper(),
        "to": (to_ccy or "").upper(),
        "rate": rate,
        "source": "frankfurter.dev (ECB reference rates)",
    }


@frappe.whitelist()
def convert_amount(amount: float, from_ccy: str, to_ccy: str = "EUR") -> dict:
    """Live-convert `amount`. Convenience for ad-hoc UI tools."""
    converted = convert(float(amount or 0), from_ccy, to_ccy)
    return {
        "from": (from_ccy or "").upper(),
        "to": (to_ccy or "").upper(),
        "amount": float(amount or 0),
        "converted": converted,
    }
