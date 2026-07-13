"""Auto-link Communications to the customer's project by mail domain.

Rule (from the LCS minimum feature set):
    Resolve the customer-side address of an email (sender for received mail,
    recipients for sent mail) to a CRM Organization via its mail domain, then
    attach the Communication to that organization's most recent active LCS
    Project. Falls back to the organization itself when no active project
    exists. Personal mail domains are ignored.

Contact backfill ("Adressbuch + Mailverkehr"): when the domain matches a
known customer but no Contact carries that address yet, a lightweight Contact
is created. Its own after_insert hooks then push it to the shared mailbox and
bind it to the organization.
"""

from __future__ import annotations

from typing import Any

import frappe

from lcs_integrations.contacts.domain_binding import (
    domain_of,
    is_bindable_domain,
    org_for_domain,
    resolve_project_for_domain,
)


def _counterparty_addresses(doc: Any) -> list[str]:
    """The customer-side addresses for this Communication."""
    if (doc.get("sent_or_received") or "Received") == "Sent":
        raw = doc.recipients or ""
        return [a.strip() for a in raw.replace(";", ",").split(",") if a.strip()]
    return [doc.sender] if doc.sender else []


def _contact_for_email(address: str | None) -> str | None:
    """Name of a Contact that carries this e-mail address (case-insensitive)."""
    if not address:
        return None
    rows = frappe.db.sql(
        "SELECT parent FROM `tabContact Email` WHERE LOWER(email_id) = %s LIMIT 1",
        (address.strip().lower(),),
    )
    return rows[0][0] if rows else None


def match_reference_for_sender(sender: str | None) -> tuple[str, str] | None:
    """Resolve a sender address to a CRM record — the import filter's
    "is this address known?" test. Imports the mail when EITHER the exact
    contact OR its company is already in the CRM:

      1. Contact match: the address belongs to an existing Contact → link to
         that contact's CRM Deal / Organization if any, else the Contact
         itself. Works even for personal-domain addresses, because an
         explicitly created contact IS the "known" signal.
      2. Company match: the sender's mail domain belongs to a CRM
         Organization → its most recent active LCS Project, else the org.

    Returns None when neither is known (mail is skipped by the sync).
    """
    address = (sender or "").strip()

    # 1. Known contact (by exact e-mail).
    contact = _contact_for_email(address)
    if contact:
        link = frappe.db.get_value(
            "Dynamic Link",
            {"parenttype": "Contact", "parent": contact, "link_doctype": "CRM Deal"},
            "link_name",
        )
        if link:
            return ("CRM Deal", link)
        org_link = frappe.db.get_value(
            "Dynamic Link",
            {"parenttype": "Contact", "parent": contact, "link_doctype": "CRM Organization"},
            "link_name",
        )
        if org_link:
            return ("CRM Organization", org_link)
        return ("Contact", contact)

    # 2. Known company (by mail domain).
    domain = domain_of(address)
    if not is_bindable_domain(domain):
        return None
    org = org_for_domain(domain)
    if not org:
        return None
    project = resolve_project_for_domain(domain)["project"]
    if project:
        return ("LCS Project", project)
    return ("CRM Organization", org)


def auto_link(doc: Any, method: str | None = None) -> None:
    if doc.get("communication_medium") != "Email" or doc.reference_doctype:
        return

    for address in _counterparty_addresses(doc):
        domain = domain_of(address)
        if not is_bindable_domain(domain):
            continue
        org = org_for_domain(domain)
        if not org:
            continue

        project = resolve_project_for_domain(domain)["project"]
        if project:
            doc.reference_doctype, doc.reference_name = "LCS Project", project
        else:
            doc.reference_doctype, doc.reference_name = "CRM Organization", org
        doc.save(ignore_permissions=True)

        _ensure_contact(address, org, full_name=_name_for(doc, address))
        return


def _name_for(doc: Any, address: str) -> str:
    """Best available display name for the counterparty."""
    if (doc.get("sent_or_received") or "Received") != "Sent" and doc.get("sender_full_name"):
        return doc.sender_full_name
    return address.split("@", 1)[0].replace(".", " ").title()


def _ensure_contact(address: str, org: str, *, full_name: str) -> None:
    """Create a Contact for an unseen customer address and link it.

    No-op when a Contact already carries the address — binding of existing
    contacts is handled by the domain-binding service / Contact hooks.
    """
    if frappe.db.exists("Contact Email", {"email_id": address}):
        return

    parts = full_name.split(" ", 1)
    contact = frappe.new_doc("Contact")
    contact.first_name = parts[0]
    contact.last_name = parts[1] if len(parts) > 1 else ""
    contact.append("email_ids", {"email_id": address, "is_primary": 1})
    contact.append("links", {"link_doctype": "CRM Organization", "link_name": org})
    contact.insert(ignore_permissions=True)
