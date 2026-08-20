"""Whitelisted API for the Outlook sync status widget."""

from __future__ import annotations

from typing import Any

import frappe


@frappe.whitelist()
def get_sync_status() -> dict[str, Any]:
    """Return the bench-wide Outlook sync state.

    Caller-side rendering only — no Graph calls. Costs a single SELECT
    on `Outlook Mailbox Binding` plus a settings cache hit.
    """
    s = frappe.get_cached_doc("LCS Outlook Sync Settings")
    bindings = frappe.get_all(
        "Outlook Mailbox Binding",
        fields=[
            "name",
            "user",
            "graph_mailbox",
            "is_active",
            "last_sync",
            "last_calendar_sync",
            "last_contacts_sync",
            "last_error",
        ],
        order_by="user asc",
    )
    return {
        "settings": {
            "shared_mailbox": s.shared_contacts_mailbox or None,
            "contact_push": bool(s.enable_contact_push),
            "inbound_contacts": bool(s.enable_inbound_contacts_sync),
            "calendar": bool(s.enable_calendar_sync),
            "teams": bool(s.enable_teams_notifications),
        },
        "bindings": bindings,
    }


@frappe.whitelist()
def list_communications(
    *,
    contact: str | None = None,
    organization: str | None = None,
    project: str | None = None,
    email: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return recent email Communications scoped to one CRM entity.

    Resolution rules:
    - `email` is the most specific selector — matches sender or recipient.
    - `contact` looks up email addresses on the Contact's `email_ids`,
      then matches sender / recipients by any of them.
    - `organization` matches Communications linked via reference_doctype.
    - `project` matches Communications linked to the LCS Project's deal,
      lead, or organization (best-effort fan-out).

    At least one selector must be provided.
    """
    if not any([contact, organization, project, email]):
        frappe.throw("Provide at least one of: contact, organization, project, email")
    limit = max(1, min(int(limit or 50), 200))

    addresses: list[str] = []
    if email:
        addresses.append(email.lower())
    if contact:
        rows = frappe.db.sql(
            """SELECT email_id FROM `tabContact Email` WHERE parent=%s""",
            (contact,),
            as_dict=True,
        )
        addresses.extend((r["email_id"] or "").lower() for r in rows if r.get("email_id"))

    filters: dict[str, Any] = {"communication_medium": "Email"}
    or_filters: list[list[Any]] = []
    if addresses:
        likes = list({a for a in addresses if a})
        for addr in likes:
            or_filters.append(["sender", "=", addr])
            or_filters.append(["recipients", "like", f"%{addr}%"])

    if organization:
        or_filters.append(["reference_doctype", "=", "CRM Organization"])

    if project:
        # Tight scope: emails linked to *this* project only. Both conditions
        # must hold, so they belong in `filters` (AND), not `or_filters`.
        filters["reference_doctype"] = "LCS Project"
        filters["reference_name"] = project

    if not or_filters and not project:
        return []

    rows = frappe.get_all(
        "Communication",
        filters=filters,
        or_filters=or_filters,
        fields=[
            "name",
            "subject",
            "sender",
            "recipients",
            "sent_or_received",
            "communication_date",
            "creation",
            "content",
            "reference_doctype",
            "reference_name",
            "user",
            "lcs_shared",
            "lcs_internal",
        ],
        order_by="communication_date desc, creation desc",
        limit=limit,
    )
    # Visibility: shared to all, or my own non-internal mail (see email_visibility).
    me = frappe.session.user
    admin = me == "Administrator"
    out = []
    for r in rows:
        if not (admin or r.get("lcs_shared") or (r.get("user") == me and not r.get("lcs_internal"))):
            continue
        r.pop("lcs_internal", None)
        r["can_release"] = 1 if r.get("user") == me else 0
        out.append(r)
    return out


@frappe.whitelist()
def trigger_resync(binding: str | None = None) -> dict[str, Any]:
    """Manually run a delta cycle.

    Without `binding`, runs the bench-wide drivers (mail + calendar).
    With `binding`, runs only that one row's mail + calendar pass.
    Returns the count of records created/updated per layer.
    """
    from . import calendar_sync, delta_service

    if binding:
        mail_created = delta_service.sync_one(binding)
        cal_upserts = calendar_sync.sync_one_calendar(binding)
        return {"binding": binding, "mail": mail_created, "calendar": cal_upserts}

    delta_service.sync_all_bindings()
    calendar_sync.sync_all_calendars()
    return {"binding": None, "ran": "all"}


@frappe.whitelist()
def test_connection(mailbox: str | None = None) -> dict[str, Any]:
    """Verify the Microsoft Graph connection from the settings UI.

    Checks the Entra env vars are present, acquires an app-only token, and
    (optionally) probes a mailbox's inbox. Read-only; returns a clear
    ok/error so the connection can be validated before enabling the sync.
    """
    from lcs_integrations.entra_config import missing_keys

    frappe.only_for(["System Manager", "Sales Manager"])

    missing = missing_keys()
    if missing:
        return {"ok": False, "error": f"Missing Entra credentials: {', '.join(missing)}"}

    from .graph_client import GraphClient, GraphClientError

    client = GraphClient()
    try:
        client._bearer()  # raises GraphClientError if credentials/consent are wrong
    except GraphClientError as exc:
        client.close()
        return {"ok": False, "error": f"Token acquisition failed: {exc}"}

    result: dict[str, Any] = {"ok": True, "token": "acquired"}
    probe = (mailbox or "").strip()
    if probe:
        try:
            client.messages_delta(probe)
            result["mailbox"] = f"{probe}: reachable"
        except GraphClientError as exc:
            result["mailbox"] = f"{probe}: {exc}"
            result["mailbox_ok"] = False
        else:
            result["mailbox_ok"] = True
    client.close()
    return result
