"""High-level WhatsApp send / receive orchestration.

`send_text` is the entry point for UI buttons (whitelisted below). It writes
an `LCS WhatsApp Message` row first (so a failed send still leaves an
audit trail), then dispatches via the client.

`process_inbound_message` is called by the webhook for each individual
message in the payload. It deduplicates by `wa_message_id`, creates the
`LCS WhatsApp Message`, mirrors a Frappe `Communication` for the CRM
timeline, and (when enabled) auto-links to a matching Contact.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from .client import WhatsAppClient, WhatsAppClientError, _normalize_phone


def _settings():
    return frappe.get_cached_doc("LCS WhatsApp Settings")


def _get_client() -> WhatsAppClient:
    s = _settings()
    if not s.enabled:
        raise WhatsAppClientError("WhatsApp integration is disabled")
    token = s.get_password("access_token") if hasattr(s, "get_password") else s.access_token
    return WhatsAppClient(access_token=token, phone_number_id=s.phone_number_id)


@frappe.whitelist()
def send_text(*, to: str, body: str, contact: str | None = None) -> dict[str, Any]:
    """Send a free-form WhatsApp message and persist the audit row.

    Returns the WhatsApp message ID and the LCS WhatsApp Message name.
    """
    if not to or not body:
        frappe.throw(_("Recipient phone and body are required"))

    msg = frappe.get_doc(
        {
            "doctype": "LCS WhatsApp Message",
            "direction": "Outbound",
            "phone_number": _normalize_phone(to),
            "contact": contact,
            "message_type": "text",
            "body": body,
            "status": "queued",
        }
    )
    msg.insert(ignore_permissions=True)

    client = _get_client()
    try:
        result = client.send_text(to=to, body=body)
    except WhatsAppClientError as exc:
        frappe.db.set_value("LCS WhatsApp Message", msg.name, {"status": "failed", "body": f"{body}\n\n[ERROR: {exc}]"})
        raise
    finally:
        client.close()

    wa_id = ""
    for entry in result.get("messages", []) or []:
        if entry.get("id"):
            wa_id = entry["id"]
            break
    frappe.db.set_value(
        "LCS WhatsApp Message",
        msg.name,
        {"status": "sent", "wa_message_id": wa_id},
    )
    _mirror_communication(msg.name, sent_or_received="Sent")
    return {"name": msg.name, "wa_message_id": wa_id}


def process_inbound_message(message: dict[str, Any], *, contacts: list[dict[str, Any]] | None = None) -> str | None:
    """Process one message from a Meta webhook payload.

    Idempotent: returns the existing row name if `wa_message_id` already
    seen. Returns the new row name otherwise.
    """
    wa_id = message.get("id")
    if not wa_id:
        return None

    existing = frappe.db.get_value("LCS WhatsApp Message", {"wa_message_id": wa_id}, "name")
    if existing:
        return existing

    from_number = _normalize_phone(message.get("from") or "")
    msg_type = message.get("type", "text")
    body = ""
    media_url = None
    if msg_type == "text":
        body = (message.get("text") or {}).get("body") or ""
    elif msg_type in {"image", "document", "audio", "video"}:
        body = ((message.get(msg_type) or {}).get("caption")) or ""
        media_url = (message.get(msg_type) or {}).get("id")  # media reference, not URL
    elif msg_type == "location":
        loc = message.get("location") or {}
        body = f"Location: {loc.get('latitude')}, {loc.get('longitude')}"
    elif msg_type == "button":
        body = (message.get("button") or {}).get("text") or ""
    else:
        body = f"[{msg_type} payload — see provider record]"

    settings = _settings()
    contact_name = None
    if settings.auto_link_to_contact:
        contact_name = _find_contact_by_phone(from_number)

    received_at = None
    ts = message.get("timestamp")
    if ts:
        try:
            received_at = frappe.utils.format_datetime(
                frappe.utils.get_datetime(int(ts)), "yyyy-MM-dd HH:mm:ss"
            )
        except Exception:  # noqa: BLE001
            received_at = None

    msg = frappe.get_doc(
        {
            "doctype": "LCS WhatsApp Message",
            "direction": "Inbound",
            "phone_number": from_number,
            "contact": contact_name,
            "wa_message_id": wa_id,
            "status": "received",
            "received_at": received_at,
            "message_type": msg_type,
            "body": body,
            "media_url": media_url,
        }
    )
    msg.insert(ignore_permissions=True)
    _mirror_communication(msg.name, sent_or_received="Received")
    return msg.name


def _find_contact_by_phone(phone: str) -> str | None:
    if not phone:
        return None
    # Match against the Frappe Contact phone child table (`phone_nos.phone`)
    rows = frappe.db.sql(
        """
        SELECT parent FROM `tabContact Phone`
        WHERE REPLACE(REPLACE(REPLACE(phone, ' ', ''), '-', ''), '+', '') = %s
        LIMIT 1
        """,
        (phone,),
        as_dict=True,
    )
    return rows[0]["parent"] if rows else None


def _mirror_communication(message_name: str, *, sent_or_received: str) -> None:
    """Reflect the WhatsApp message as a Frappe Communication for the CRM timeline."""
    msg = frappe.get_doc("LCS WhatsApp Message", message_name)
    comm = frappe.get_doc(
        {
            "doctype": "Communication",
            "communication_medium": "Chat",
            "communication_type": "Communication",
            "sent_or_received": sent_or_received,
            "sender": msg.phone_number,
            "recipients": msg.phone_number,
            "subject": f"WhatsApp ({msg.message_type})",
            "content": msg.body or "",
            "message_id": msg.wa_message_id or msg.name,
        }
    )
    if msg.contact:
        comm.reference_doctype = "Contact"
        comm.reference_name = msg.contact
    comm.insert(ignore_permissions=True)
    frappe.db.set_value("LCS WhatsApp Message", msg.name, "communication", comm.name)


def update_message_status(wa_message_id: str, status: str) -> None:
    """Apply a delivery / read / failed status update from a webhook."""
    name = frappe.db.get_value("LCS WhatsApp Message", {"wa_message_id": wa_message_id}, "name")
    if not name:
        return
    frappe.db.set_value("LCS WhatsApp Message", name, "status", status)
