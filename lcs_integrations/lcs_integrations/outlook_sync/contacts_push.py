"""Push Frappe Contact records to the shared Sales mailbox address book.

One-way: Frappe is the source of truth. Each pushed contact stores its Graph
contact ID in the Custom Field `graph_contact_id`, which is what we use to
distinguish create-vs-update and to delete on Frappe-side trash.

Inbound edits made directly in the shared mailbox come back through
`contacts_sync.py` (separate module).
"""

from __future__ import annotations

from typing import Any

import frappe

from .graph_client import GraphClient, GraphClientError


def _settings():
    return frappe.get_cached_doc("LCS Outlook Sync Settings")


def _is_active() -> tuple[bool, str | None]:
    s = _settings()
    if not s.enable_contact_push:
        return False, None
    mailbox = (s.shared_contacts_mailbox or "").strip()
    if not mailbox:
        return False, None
    return True, mailbox


def _to_graph_payload(contact) -> dict[str, Any]:
    """Map a Frappe Contact to the Microsoft Graph contact resource."""
    payload: dict[str, Any] = {
        "givenName": contact.first_name or "",
        "surname": contact.last_name or "",
    }
    if contact.full_name:
        payload["displayName"] = contact.full_name
    if contact.company_name:
        payload["companyName"] = contact.company_name
    if contact.designation:
        payload["jobTitle"] = contact.designation

    emails = []
    for row in contact.get("email_ids") or []:
        addr = (row.email_id or "").strip()
        if addr:
            emails.append({"address": addr, "name": contact.full_name or addr})
    if emails:
        payload["emailAddresses"] = emails

    phones_business: list[str] = []
    phones_mobile: list[str] = []
    for row in contact.get("phone_nos") or []:
        num = (row.phone or "").strip()
        if not num:
            continue
        if (row.get("is_primary_mobile_no") or 0):
            phones_mobile.append(num)
        else:
            phones_business.append(num)
    if phones_business:
        payload["businessPhones"] = phones_business
    if phones_mobile:
        payload["mobilePhone"] = phones_mobile[0]

    return payload


def on_contact_after_insert(doc, method=None) -> None:
    if getattr(doc, "_lcs_skip_push", False):
        return
    push_contact(doc.name)


def on_contact_on_update(doc, method=None) -> None:
    if getattr(doc, "_lcs_skip_push", False):
        return
    push_contact(doc.name)


def on_contact_on_trash(doc, method=None) -> None:
    delete_contact(doc.name, getattr(doc, "graph_contact_id", None))


def push_contact(contact_name: str) -> str | None:
    """Create or update the contact in the shared mailbox.

    Returns the Graph contact ID, or None if push is disabled / failed.
    """
    active, mailbox = _is_active()
    if not active:
        return None

    contact = frappe.get_doc("Contact", contact_name)
    payload = _to_graph_payload(contact)
    graph_id = getattr(contact, "graph_contact_id", None)

    client = GraphClient()
    try:
        if graph_id:
            client.contact_update(mailbox, graph_id, payload)
            new_id = graph_id
        else:
            result = client.contact_create(mailbox, payload)
            new_id = result.get("id")
            if new_id:
                frappe.db.set_value("Contact", contact_name, "graph_contact_id", new_id)
        if new_id and contact.image:
            _push_photo(client, mailbox, new_id, contact.image)
    except GraphClientError as exc:
        frappe.log_error(title="contacts_push", message=f"{contact_name}: {exc}")
        return None
    finally:
        client.close()
    return new_id


def _push_photo(client: GraphClient, mailbox: str, graph_id: str, image_url: str) -> None:
    """Upload the Frappe Contact image to the mailbox contact."""
    file_name = frappe.db.get_value("File", {"file_url": image_url}, "name")
    if not file_name:
        return
    content = frappe.get_doc("File", file_name).get_content()
    if content:
        client.contact_photo_put(mailbox, graph_id, content)


def delete_contact(contact_name: str, graph_id: str | None) -> None:
    if not graph_id:
        return
    active, mailbox = _is_active()
    if not active:
        return

    client = GraphClient()
    try:
        client.contact_delete(mailbox, graph_id)
    except GraphClientError as exc:
        frappe.log_error(title="contacts_push", message=f"delete {contact_name}: {exc}")
    finally:
        client.close()
