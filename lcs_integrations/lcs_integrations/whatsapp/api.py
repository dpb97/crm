"""Whitelisted API for the WhatsApp panel widget.

Read-side helpers — the write path (`send_text`) lives in service.py and
is already whitelisted there.
"""

from __future__ import annotations

from typing import Any

import frappe


@frappe.whitelist()
def list_messages(
    *,
    contact: str | None = None,
    phone: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return the most recent WhatsApp messages for a contact or phone.

    Either `contact` or `phone` must be provided. Limit is capped at 200
    to keep payloads bounded.
    """
    if not contact and not phone:
        frappe.throw("contact or phone is required")
    limit = max(1, min(int(limit or 50), 200))

    filters: dict[str, Any] = {}
    if contact:
        filters["contact"] = contact
    if phone:
        filters["phone_number"] = ["like", f"%{phone.lstrip('+')}%"]

    rows = frappe.get_all(
        "LCS WhatsApp Message",
        filters=filters,
        fields=[
            "name",
            "direction",
            "phone_number",
            "contact",
            "wa_message_id",
            "status",
            "received_at",
            "creation",
            "message_type",
            "body",
        ],
        order_by="creation desc",
        limit=limit,
    )
    return rows


@frappe.whitelist()
def settings_summary() -> dict[str, Any]:
    """Lightweight summary of the WhatsApp settings — enough for the panel
    to know whether sending is allowed."""
    s = frappe.get_cached_doc("LCS WhatsApp Settings")
    return {
        "enabled": bool(s.enabled),
        "provider": s.provider,
        "phone_number_id": s.phone_number_id or None,
    }
