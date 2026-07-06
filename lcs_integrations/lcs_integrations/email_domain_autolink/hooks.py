"""Auto-link incoming Communications to a Customer by sender domain.

Rule (from the LCS minimum feature set):
    If the sender domain matches the email domain of an existing Customer /
    CRM Deal primary contact, attach the Communication to that record.
    Otherwise leave it unattached — manual linking through a UI button is the
    fallback.
"""

from __future__ import annotations

from typing import Any

import frappe

_PERSONAL_DOMAINS = frozenset({
    "gmail.com", "googlemail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "gmx.de", "gmx.at", "gmx.net", "web.de", "t-online.de", "icloud.com",
})


def _domain(address: str) -> str | None:
    if not address or "@" not in address:
        return None
    return address.rsplit("@", 1)[-1].lower().strip()


def match_reference_for_sender(sender: str | None) -> tuple[str, str] | None:
    """Resolve a sender address to a linked CRM record via its mail domain.

    Returns (reference_doctype, reference_name) when the domain belongs to a
    Contact with a primary company e-mail that is linked to a CRM Deal —
    otherwise None. Shared by the Communication after_insert hook (auto_link)
    and by the Outlook delta sync as its import filter, so "known domain"
    means the same thing everywhere.
    """
    domain = _domain(sender or "")
    if not domain or domain in _PERSONAL_DOMAINS:
        return None
    contact = frappe.db.sql(
        """
        SELECT parent FROM `tabContact Email`
        WHERE email_id LIKE %(pattern)s AND is_primary = 1
        LIMIT 1
        """,
        {"pattern": f"%@{domain}"},
        as_dict=True,
    )
    if not contact:
        return None
    link = frappe.db.get_value(
        "Dynamic Link",
        {"parenttype": "Contact", "parent": contact[0]["parent"],
         "link_doctype": ("in", ["CRM Deal", "Contact"])},
        ("link_doctype", "link_name"),
    )
    return link or None


def auto_link(doc: Any, method: str | None = None) -> None:
    if doc.get("communication_medium") != "Email" or doc.reference_doctype:
        return
    link = match_reference_for_sender(doc.sender)
    if link:
        doc.reference_doctype, doc.reference_name = link
        doc.save(ignore_permissions=True)
