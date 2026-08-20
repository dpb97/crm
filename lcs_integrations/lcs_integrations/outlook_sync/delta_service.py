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
from lcs_integrations.visibility import email_visibility

from .graph_client import GraphClient, GraphClientError


def _graph_datetime(value):
    """Parse a Graph ISO-8601 UTC timestamp (e.g. '2026-08-15T09:30:00Z') into a
    naive datetime in the site's timezone — used for Communication.communication_date
    so the mail carries its real received/sent time, not the sync time."""
    if not value:
        return None
    import datetime
    try:
        dt = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None
    dt = dt.replace(tzinfo=None)  # naive UTC
    try:
        return frappe.utils.convert_utc_to_system_timezone(dt).replace(tzinfo=None)
    except Exception:
        return dt


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


def _delete_communication(message_id: str) -> bool:
    """Remove the CRM copy of a mailbox message that was deleted in Outlook,
    together with its timeline links. Returns True if one was deleted."""
    name = frappe.db.get_value("Communication", {"message_id": message_id}, "name")
    if not name:
        return False
    frappe.db.delete("Communication Link", {"parent": name})
    frappe.delete_doc("Communication", name, ignore_permissions=True, delete_permanently=True, force=True)
    return True


def sync_one(binding_name: str) -> int:
    """Run one delta sync cycle. Returns number of Communications created.
    Also mirrors Outlook deletions into the CRM (see the @removed handling)."""
    binding = frappe.get_doc("Outlook Mailbox Binding", binding_name)
    client = GraphClient()
    created = 0
    deleted = 0
    deleted_items_id = None  # resolved lazily, only if a removal shows up
    try:
        page = client.messages_delta(binding.graph_mailbox, binding.delta_token)
        for message in page.get("value", []):
            if message.get("@removed"):
                # The Inbox delta flags an item @removed for BOTH a real deletion
                # AND a move to another folder. Only mirror a real deletion: the
                # message is gone from the mailbox (404) or now sits in Deleted
                # Items. A move to any other folder keeps the CRM copy.
                gid = message.get("id")
                if not gid:
                    continue
                if deleted_items_id is None:
                    deleted_items_id = client.well_known_folder_id(binding.graph_mailbox, "deleteditems") or ""
                folder = client.get_message_folder(binding.graph_mailbox, gid)
                if (folder is None or (deleted_items_id and folder == deleted_items_id)) and _delete_communication(gid):
                    deleted += 1
                continue
            if _persist_message(
                binding.user, message,
                only_known=bool(binding.get("import_only_known_domains")),
            ):
                created += 1
    finally:
        client.close()

    if deleted:
        frappe.logger().info(f"outlook sync: mirrored {deleted} deletion(s) for {binding.graph_mailbox}")

    # Persist the new delta pointer so the next run is incremental.
    next_link = page.get("@odata.deltaLink") or page.get("@odata.nextLink")
    frappe.db.set_value(
        "Outlook Mailbox Binding", binding.name,
        {"delta_token": next_link, "last_sync": frappe.utils.now_datetime(), "last_error": None},
    )
    return created


def _mail_sync_disabled(emails):
    """True if any participant email belongs to a Contact opted out of mail sync."""
    for e in emails:
        if not e:
            continue
        for parent in frappe.get_all("Contact Email", filters={"email_id": e}, pluck="parent"):
            if frappe.db.get_value("Contact", parent, "lcs_mail_sync") == 0:
                return True
    return False


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
    # Keep only recipients / CC that are valid SMTP addresses; distribution-list
    # display names and X.500 recipients would otherwise fail validation.
    recipients = ", ".join(
        addr for addr in (
            (r.get("emailAddress", {}) or {}).get("address", "")
            for r in message.get("toRecipients", [])
        ) if addr and frappe.utils.validate_email_address(addr)
    )
    cc = ", ".join(
        addr for addr in (
            (r.get("emailAddress", {}) or {}).get("address", "")
            for r in message.get("ccRecipients", [])
        ) if addr and frappe.utils.validate_email_address(addr)
    )
    subject = message.get("subject") or "(no subject)"
    # Visibility / noise rules (see visibility.email_visibility):
    #   * `P` = project number/name in subject OR crm@lcs-group.com in CC → shared
    #   * internal → internal mail is dropped entirely unless `P`
    #   * a `P` mail is always relevant → it bypasses the only_known sender filter
    flags = email_visibility.compute_flags(sender, subject, recipients, cc)
    if flags["lcs_internal"] and not flags["lcs_shared"]:
        return False
    if not flags["lcs_shared"] and only_known and not match_reference_for_sender(sender):
        return False
    # LCS: honor the per-contact Mail-Sync opt-out (lcs_mail_sync=0).
    _parts = [sender] + [a.strip() for a in recipients.split(",") if a.strip()]
    if _mail_sync_disabled(_parts):
        return False
    sent_or_received = "Received" if message.get("isDraft") is False else "Sent"
    # Real timestamp from Graph (received for inbound, sent for outbound), so the
    # CRM shows the actual mail date instead of the moment it was synced.
    comm_date = (
        _graph_datetime(message.get("receivedDateTime") if sent_or_received == "Received" else message.get("sentDateTime"))
        or _graph_datetime(message.get("receivedDateTime"))
        or _graph_datetime(message.get("sentDateTime"))
    )
    comm = frappe.get_doc({
        "doctype": "Communication",
        "communication_medium": "Email",
        "sent_or_received": sent_or_received,
        "sender": sender,
        "recipients": recipients,
        "cc": cc,
        "subject": subject,
        "content": message.get("body", {}).get("content") or "",
        "message_id": graph_id,
        "user": user,
        "communication_date": comm_date,
        "lcs_conversation_id": message.get("conversationId"),
        "lcs_internal": flags["lcs_internal"],
        "lcs_shared": flags["lcs_shared"],
    })
    comm.insert(ignore_permissions=True)
    return True


@frappe.whitelist()
def repair_communication_dates(limit=100000):
    """One-off backfill of the real received/sent date onto already-synced mail
    that was stamped with the sync time. Fetches each message's timestamps from
    Graph by its stored id + mailbox and updates communication_date in place."""
    gc = GraphClient()
    rows = frappe.get_all(
        "Communication",
        filters={"communication_type": "Communication", "message_id": ["is", "set"]},
        fields=["name", "message_id", "user"],
        limit=int(limit),
    )
    fixed = failed = 0
    for i, r in enumerate(rows):
        mailbox = r.get("user")
        gid = r.get("message_id")
        if not mailbox or not gid:
            failed += 1
            continue
        try:
            m = gc.message_dates(mailbox, gid)
        except Exception:
            failed += 1
            continue
        dt = _graph_datetime(m.get("receivedDateTime")) or _graph_datetime(m.get("sentDateTime"))
        if dt:
            frappe.db.set_value("Communication", r["name"], "communication_date", dt, update_modified=False)
            fixed += 1
        if i % 100 == 0:
            frappe.db.commit()
    frappe.db.commit()
    return {"total": len(rows), "fixed": fixed, "failed": failed}
