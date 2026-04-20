"""HTTP entry points for the abas integration.

Every endpoint is guarded by `@frappe.whitelist` and — for inbound webhooks —
by HMAC verification before any business logic runs.
"""

from __future__ import annotations

import os

import frappe

from .client import AbasClient
from .service import handle_delivery_webhook, push_customer


@frappe.whitelist(methods=["POST"])
def push_customer_endpoint(reference_doctype: str, reference_name: str) -> dict:
    """Trigger a manual customer push from the UI / bench console."""
    if reference_doctype not in {"Contact", "CRM Deal"}:
        frappe.throw("Only Contact or CRM Deal can be pushed to abas.")
    abas_id = push_customer(reference_doctype, reference_name)
    return {"abas_id": abas_id}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def webhook() -> dict:
    """Receive delivery-status updates from abas."""
    raw_body = frappe.request.get_data() or b""
    ts = frappe.get_request_header("X-LCS-Timestamp") or ""
    sig = frappe.get_request_header("X-LCS-Signature") or ""
    key = os.environ["ABAS_HMAC_KEY"].encode()
    if not AbasClient.verify_inbound(raw_body, ts, sig, key):
        frappe.throw("Invalid signature", frappe.AuthenticationError)
    payload = frappe.parse_json(raw_body)
    handle_delivery_webhook(payload)
    return {"ok": True}
