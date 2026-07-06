"""Webhook endpoint for Meta WhatsApp Cloud API.

Configured in Meta Business → Webhooks → Configuration:
  Callback URL : https://<host>/api/method/lcs_integrations.whatsapp.webhook.handle
  Verify token : value from `LCS WhatsApp Settings.webhook_verify_token`
  Subscribe to : messages, message_status

Two flows:
- GET  with hub.mode=subscribe → echo `hub.challenge` if the verify token matches
- POST with the messaging payload → fan out to `service.process_inbound_message`
                                    or `service.update_message_status`
"""

from __future__ import annotations

from typing import Any

import frappe

from . import service


@frappe.whitelist(allow_guest=True)
def handle() -> Any:
    """Single endpoint for both verification (GET) and delivery (POST)."""
    method = (frappe.local.request.method or "GET").upper()
    if method == "GET":
        return _verify()
    if method == "POST":
        return _ingest()
    frappe.local.response["http_status_code"] = 405
    return {"error": "method not allowed"}


def _verify() -> str:
    """Meta hub-challenge verification."""
    args = frappe.local.form_dict
    mode = args.get("hub.mode")
    token = args.get("hub.verify_token")
    challenge = args.get("hub.challenge", "")

    settings = frappe.get_cached_doc("LCS WhatsApp Settings")
    expected = settings.get_password("webhook_verify_token") if hasattr(settings, "get_password") else settings.webhook_verify_token

    if mode == "subscribe" and token and expected and token == expected:
        return challenge
    frappe.local.response["http_status_code"] = 403
    return "forbidden"


def _ingest() -> dict[str, Any]:
    """Walk the Meta payload and dispatch to the service layer."""
    try:
        payload = frappe.parse_json(frappe.request.data) if frappe.request.data else {}
    except Exception:  # noqa: BLE001
        payload = {}

    handled = 0
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            value = change.get("value", {}) or {}

            # Message statuses (delivery / read / failed)
            for status in value.get("statuses", []) or []:
                wa_id = status.get("id")
                state = status.get("status")
                if wa_id and state:
                    service.update_message_status(wa_id, state)
                    handled += 1

            # Inbound messages
            for message in value.get("messages", []) or []:
                if service.process_inbound_message(message, contacts=value.get("contacts")):
                    handled += 1

    frappe.db.commit()
    return {"handled": handled}
