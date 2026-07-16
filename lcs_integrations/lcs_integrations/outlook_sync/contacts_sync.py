"""Inbound contact sync: shared mailbox contacts -> Frappe Contact.

Pulls the shared mailbox's address book delta and reflects creations / edits
into Frappe. The shared mailbox UPN comes from `LCS Outlook Sync Settings`.

Loop avoidance: Frappe `Contact` already has a `graph_contact_id` field
(installed by patch). The push side (contacts_push.py) is what writes to
Graph; the pull side here only writes to Frappe. To break a potential
echo, we don't re-push contacts that we've just pulled — the matching is
by graph_contact_id, and the push-on-update hook is a no-op when the doc
already has a Graph ID and the field set has not changed beyond what we
just imported.
"""

from __future__ import annotations

from typing import Any

import frappe

from .graph_client import GraphClient, GraphClientError


# Sentinel field on `Contact` so the push hook can detect "this update
# came from inbound sync" and skip re-pushing.
INBOUND_FLAG = "_lcs_skip_push"


def _settings():
    return frappe.get_cached_doc("LCS Outlook Sync Settings")


def sync_inbound_contacts() -> int:
    """Driver — looks up settings and runs one delta cycle."""
    s = _settings()
    if not s.enable_inbound_contacts_sync:
        return 0
    mailbox = (s.shared_contacts_mailbox or "").strip()
    if not mailbox:
        return 0

    # Use the first active binding's contacts_delta_token as our cursor —
    # the shared mailbox is global, not per-user, so we just need any
    # bench-wide place to remember the cursor. We re-use the binding row
    # that matches the shared mailbox UPN if one exists; otherwise we
    # autocreate a marker binding.
    cursor_row = _get_cursor_row(mailbox)

    client = GraphClient()
    try:
        try:
            page = client.contacts_delta(mailbox, cursor_row.contacts_delta_token)
        except GraphClientError as exc:
            frappe.log_error(title="contacts_sync", message=str(exc))
            frappe.db.set_value(
                "Outlook Mailbox Binding", cursor_row.name, "last_error", str(exc)
            )
            return 0

        upserts = 0
        for entry in page.get("value", []):
            if _persist_contact(entry, client, mailbox):
                upserts += 1
    finally:
        client.close()

    next_link = page.get("@odata.deltaLink") or page.get("@odata.nextLink")
    frappe.db.set_value(
        "Outlook Mailbox Binding",
        cursor_row.name,
        {
            "contacts_delta_token": next_link,
            "last_contacts_sync": frappe.utils.now_datetime(),
            "last_error": None,
        },
    )
    return upserts


def _get_cursor_row(mailbox: str):
    name = frappe.db.get_value("Outlook Mailbox Binding", {"graph_mailbox": mailbox}, "name")
    if name:
        return frappe.get_doc("Outlook Mailbox Binding", name)

    # Autocreate a marker row owned by the bench Administrator so we have
    # a stable place for the cursor.
    doc = frappe.get_doc(
        {
            "doctype": "Outlook Mailbox Binding",
            "user": "Administrator",
            "graph_mailbox": mailbox,
            "is_active": 1,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc


def _persist_contact(entry: dict[str, Any], client: GraphClient, mailbox: str) -> bool:
    graph_id = entry.get("id")
    if not graph_id:
        return False

    if entry.get("@removed"):
        existing = frappe.db.get_value("Contact", {"graph_contact_id": graph_id}, "name")
        if existing:
            frappe.delete_doc("Contact", existing, ignore_permissions=True, delete_permanently=False)
            return True
        return False

    full_name = entry.get("displayName") or entry.get("givenName") or ""
    given = entry.get("givenName") or ""
    family = entry.get("surname") or ""
    company = entry.get("companyName") or ""
    title = entry.get("jobTitle") or ""
    emails = [e.get("address") for e in (entry.get("emailAddresses") or []) if e.get("address")]
    business_phones = entry.get("businessPhones") or []
    mobile_phone = entry.get("mobilePhone")

    existing_name = frappe.db.get_value("Contact", {"graph_contact_id": graph_id}, "name")
    if existing_name:
        contact = frappe.get_doc("Contact", existing_name)
    else:
        contact = frappe.new_doc("Contact")
        contact.graph_contact_id = graph_id

    contact.first_name = given
    contact.last_name = family
    contact.full_name = full_name or f"{given} {family}".strip()
    contact.company_name = company
    contact.designation = title

    # Email + phone children: replace wholesale to keep parity with Graph.
    contact.set("email_ids", [])
    for i, addr in enumerate(emails):
        contact.append("email_ids", {"email_id": addr, "is_primary": 1 if i == 0 else 0})

    contact.set("phone_nos", [])
    for i, num in enumerate(business_phones):
        contact.append("phone_nos", {"phone": num, "is_primary_phone": 1 if i == 0 else 0})
    if mobile_phone:
        contact.append("phone_nos", {"phone": mobile_phone, "is_primary_mobile_no": 1})

    # Mark as inbound so the push hook short-circuits.
    setattr(contact, INBOUND_FLAG, True)

    if existing_name:
        contact.save(ignore_permissions=True)
    else:
        contact.insert(ignore_permissions=True)

    # Pull the contact photo once — only when we don't already have an image.
    if not contact.image:
        _pull_photo(contact.name, graph_id, client, mailbox)
    return True


def _pull_photo(contact_name: str, graph_id: str, client: GraphClient, mailbox: str) -> None:
    """Fetch the Graph contact photo and attach it as the Contact image."""
    try:
        image = client.contact_photo_get(mailbox, graph_id)
    except GraphClientError as exc:
        frappe.log_error(title="contacts_sync", message=f"photo {contact_name}: {exc}")
        return
    if not image:
        return

    file_doc = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": f"{contact_name}.jpg",
            "content": image,
            "attached_to_doctype": "Contact",
            "attached_to_name": contact_name,
            "attached_to_field": "image",
            "is_private": 0,
        }
    ).insert(ignore_permissions=True)
    frappe.db.set_value("Contact", contact_name, "image", file_doc.file_url)
