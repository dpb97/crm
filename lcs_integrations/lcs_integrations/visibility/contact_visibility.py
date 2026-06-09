"""Owner-only Contact visibility until release.

A Contact is visible only to its creator (owner) until `lcs_released` is
set. After release it follows normal Contact permissions. Exceptions that
see a contact regardless of release:

- the owner (creator)
- System Manager / Administrator
- users the contact is explicitly shared with (DocShare)

Only the creator may release their own contact (System Manager may too,
as an administrative override).

Two enforcement layers, same as visibility.service:
1. permission_query_conditions — row-level filter for lists/reports/APIs.
2. has_permission — document-level read check.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.share import get_shared


def _is_privileged(user: str) -> bool:
    return user == "Administrator" or "System Manager" in frappe.get_roles(user)


def get_permission_query_conditions(user: str | None = None) -> str:
    """Restrict Contact lists to owner + released + explicitly shared."""
    user = user or frappe.session.user
    if _is_privileged(user):
        return ""

    conditions = [
        f"`tabContact`.owner = {frappe.db.escape(user)}",
        "`tabContact`.lcs_released = 1",
    ]
    shared = get_shared("Contact", user)
    if shared:
        names = ", ".join(frappe.db.escape(name) for name in shared)
        conditions.append(f"`tabContact`.name in ({names})")

    return "(" + " or ".join(conditions) + ")"


def has_permission(doc: Any, ptype: str = "read", user: str | None = None) -> bool | None:
    """Deny read on an unreleased contact for everyone but its creator,
    shared users, and System Managers. Returns None (no opinion) for the
    allowed cases and for non-read ptypes so standard role perms apply.
    """
    if ptype not in ("read", "select"):
        return None

    user = user or frappe.session.user
    if _is_privileged(user):
        return None
    if doc.owner == user or getattr(doc, "lcs_released", 0):
        return None
    if doc.name in get_shared("Contact", user):
        return None

    return False


@frappe.whitelist()
def release_contact(contact: str) -> dict[str, Any]:
    """Release a contact so the team can see it. Creator-only."""
    doc = frappe.get_doc("Contact", contact)
    if doc.owner != frappe.session.user and not _is_privileged(frappe.session.user):
        frappe.throw(_("Nur der Ersteller kann diesen Kontakt freigeben."), frappe.PermissionError)
    if doc.lcs_released:
        return {"ok": True, "released": True, "already": True}

    doc.lcs_released = 1
    doc.lcs_released_by = frappe.session.user
    doc.lcs_released_on = frappe.utils.now_datetime()
    doc.save(ignore_permissions=True)
    return {"ok": True, "released": True}


@frappe.whitelist()
def unrelease_contact(contact: str) -> dict[str, Any]:
    """Make a released contact private to its creator again. Creator-only."""
    doc = frappe.get_doc("Contact", contact)
    if doc.owner != frappe.session.user and not _is_privileged(frappe.session.user):
        frappe.throw(_("Nur der Ersteller kann die Freigabe zurücknehmen."), frappe.PermissionError)

    doc.lcs_released = 0
    doc.lcs_released_by = None
    doc.lcs_released_on = None
    doc.save(ignore_permissions=True)
    return {"ok": True, "released": False}
