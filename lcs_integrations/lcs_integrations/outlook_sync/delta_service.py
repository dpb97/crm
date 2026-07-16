"""Periodic Outlook delta-sync driver.

One row in `Outlook Mailbox Binding` per mailbox; this module walks the delta
and creates Frappe `Communication` records for each new message. The actual
Customer/Deal auto-linking happens in the `email_domain_autolink` hook that
fires on Communication insert.
"""

from __future__ import annotations

from typing import Any

import frappe

from lcs_integrations.email_domain_autolink.hooks import match_reference_for_sender

from .graph_client import GraphClient, GraphClientError


def sync_all_bindings() -> None:
    bindings = frappe.get_all(
        "Outlook Mailbox Binding",
        filters={"is_active": 1},
        fields=["name", "user", "graph_mailbox", "delta_token"],
    )
    for binding in bindings:
        try:
            sync_one(binding.name)
        except GraphClientError as exc:
            frappe.db.set_value("Outlook Mailbox Binding", binding.name, "last_error", str(exc))
            frappe.log_error(title="outlook_sync", message=str(exc))


def sync_one(binding_name: str) -> int:
    """Run one delta sync cycle. Returns number of Communications created."""
    binding = frappe.get_doc("Outlook Mailbox Binding", binding_name)
    client = GraphClient()
    try:
        page = client.messages_delta(binding.graph_mailbox, binding.delta_token)
    finally:
        client.close()

    created = 0
    for message in page.get("value", []):
        if _persist_message(
            binding.user, message,
            only_known=bool(binding.get("import_only_known_domains")),
        ):
            created += 1

    # Persist the new delta pointer so the next run is incremental.
    next_link = page.get("@odata.deltaLink") or page.get("@odata.nextLink")
    frappe.db.set_value(
        "Outlook Mailbox Binding", binding.name,
        {"delta_token": next_link, "last_sync": frappe.utils.now_datetime(), "last_error": None},
    )
    return created


def _persist_message(user: str, message: dict[str, Any], only_known: bool = True) -> bool:
    graph_id = message.get("id")
    if not graph_id:
        return False
    # Deduplicate by Graph message ID stored in `message_id`.
    if frappe.db.exists("Communication", {"message_id": graph_id}):
        return False
    sender_raw = (message.get("from", {}).get("emailAddress", {}).get("address") or "").lower()
    # Historical mail can carry non-SMTP senders (X.500/EX addresses, empty
    # from). Frappe's Communication.validate rejects those hard, so normalise
    # first and skip anything without a usable sender address.
    sender = frappe.utils.validate_email_address(sender_raw) or ""
    if not sender:
        return False
    # Skip mail sent from our own company domain — internal correspondence is
    # noise in a customer-facing CRM. "Own domain" = the mailbox owner's domain.
    own_domain = user.rsplit("@", 1)[-1].lower() if "@" in (user or "") else ""
    if own_domain and sender.lower().endswith("@" + own_domain):
        return False
    # Import filter: skip mail whose sender domain is not linked to any CRM
    # contact/deal — keeps private and unrelated mail out of the CRM entirely
    # (same matching rule the auto-link hook applies after insert).
    if only_known and not match_reference_for_sender(sender):
        return False
    # Keep only recipients that are valid SMTP addresses; distribution-list
    # display names and X.500 recipients would otherwise fail validation.
    recipients = ", ".join(
        addr for addr in (
            (r.get("emailAddress", {}) or {}).get("address", "")
            for r in message.get("toRecipients", [])
        ) if addr and frappe.utils.validate_email_address(addr)
    )
    comm = frappe.get_doc({
        "doctype": "Communication",
        "communication_medium": "Email",
        "sent_or_received": "Received" if message.get("isDraft") is False else "Sent",
        "sender": sender,
        "recipients": recipients,
        "subject": message.get("subject") or "(no subject)",
        "content": message.get("body", {}).get("content") or "",
        "message_id": graph_id,
        "user": user,
    })
    comm.insert(ignore_permissions=True)
    return True
