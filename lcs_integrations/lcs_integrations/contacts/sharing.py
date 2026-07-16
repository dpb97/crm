"""Share a Contact with other users.

Thin whitelisted wrapper around Frappe's native DocShare so the CRM SPA can
offer a "Share contact" action. We don't reinvent permissions — sharing
requires `share` permission on the Contact, exactly like Desk.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.share import add as share_add, remove as share_remove


def _guard(contact: str) -> None:
    if not frappe.db.exists("Contact", contact):
        frappe.throw(f"Contact {contact} not found")
    if not frappe.has_permission("Contact", ptype="share", doc=contact):
        frappe.throw("Not permitted to share this contact", frappe.PermissionError)


@frappe.whitelist()
def share_contact(contact: str, user: str, read: int = 1, write: int = 0, share: int = 0) -> dict[str, Any]:
    """Grant `user` access to a Contact. Idempotent — re-sharing updates the
    existing DocShare row's flags.
    """
    _guard(contact)
    if not frappe.db.exists("User", user):
        frappe.throw(f"User {user} not found")

    share_add(
        "Contact",
        contact,
        user,
        read=int(read),
        write=int(write),
        share=int(share),
        flags={"ignore_share_permission": True},  # we already checked above
    )
    return {"ok": True, "contact": contact, "user": user}


@frappe.whitelist()
def unshare_contact(contact: str, user: str) -> dict[str, Any]:
    """Revoke a user's shared access to a Contact."""
    _guard(contact)
    share_remove("Contact", contact, user)
    return {"ok": True, "contact": contact, "user": user}


@frappe.whitelist()
def list_contact_shares(contact: str) -> list[dict[str, Any]]:
    """Users this Contact is shared with (excludes the owner)."""
    if not frappe.has_permission("Contact", ptype="read", doc=contact):
        frappe.throw("Not permitted", frappe.PermissionError)

    return frappe.get_all(
        "DocShare",
        filters={"share_doctype": "Contact", "share_name": contact},
        fields=["user", "read", "write", "share", "everyone"],
        order_by="creation asc",
    )
