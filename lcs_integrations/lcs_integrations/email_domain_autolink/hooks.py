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


def auto_link(doc: Any, method: str | None = None) -> None:
    if doc.get("communication_medium") != "Email" or doc.reference_doctype:
        return
    domain = _domain(doc.sender or "")
    if not domain or domain in _PERSONAL_DOMAINS:
        return
    # Find any Contact whose primary email shares this domain.
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
        return
    contact_name = contact[0]["parent"]
    link = frappe.db.get_value(
        "Dynamic Link",
        {"parenttype": "Contact", "parent": contact_name, "link_doctype": ("in", ["CRM Deal", "Contact"])},
        ("link_doctype", "link_name"),
    )
    if link:
        doc.reference_doctype, doc.reference_name = link
        doc.save(ignore_permissions=True)
