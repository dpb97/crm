"""Teams-based calling for the CRM — replaces the Twilio/Exotel dialer.

Instead of a PSTN provider, "calling" a contact opens a Microsoft Teams
call (VoIP by e-mail, or PSTN via Teams Phone by number) through a Teams
deep link, and records the attempt as a CRM Call Log with medium="Teams"
so it shows up in the Calls tab / Call Logs like any other call.

No Graph credentials required for the click-to-call + logging path — the
deep link is opened client-side. (A future Graph `callRecords` sync could
back-fill real duration/outcome once CallRecords.Read.All consent exists;
out of scope here.)
"""

from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import now_datetime

_TEAMS_CALL = "https://teams.microsoft.com/l/call/0/0?users="


def _e164(raw: str) -> str:
    """Digits with a single leading '+' (Teams PSTN wants +<country><number>)."""
    cleaned = "".join(ch for ch in (raw or "") if ch.isdigit() or ch == "+")
    return "+" + cleaned.lstrip("+") if cleaned else ""


def _deep_link(email: str | None, phone: str | None) -> str:
    """Teams call target. Prefer a VoIP call to the Teams user by e-mail;
    fall back to a PSTN call (needs Teams Phone) via the '4:' number prefix.
    """
    if email:
        return _TEAMS_CALL + quote(email)
    if phone:
        return _TEAMS_CALL + quote("4:" + _e164(phone))
    return ""


@frappe.whitelist()
def start_teams_call(
    reference_doctype: str | None = None,
    reference_name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
) -> dict:
    """Open a Teams call and log it. Returns the deep link for the client to
    launch plus the created Call Log name (so it can be completed later)."""
    url = _deep_link(email, phone)
    if not url:
        frappe.throw(_("No phone number or Teams address for this contact."))

    call_log = None
    if frappe.db.exists("DocType", "CRM Call Log"):
        doc = frappe.new_doc("CRM Call Log")
        doc.id = frappe.generate_hash(length=12)
        doc.type = "Outgoing"
        doc.status = "Initiated"
        doc.medium = "Teams"
        doc.set("from", frappe.session.user)
        doc.to = email or _e164(phone)
        doc.caller = frappe.session.user
        doc.start_time = now_datetime()
        if reference_doctype and reference_name:
            doc.reference_doctype = reference_doctype
            doc.reference_docname = reference_name
        doc.insert(ignore_permissions=True)
        call_log = doc.name

    return {"url": url, "call_log": call_log}


@frappe.whitelist()
def complete_teams_call(
    call_log: str,
    status: str = "Completed",
    duration: float | int | None = None,
    note: str | None = None,
) -> dict:
    """Mark a logged Teams call as finished — the SPA calls this when the
    user records the outcome (Teams itself gives no callback without a
    Graph subscription)."""
    if not frappe.db.exists("CRM Call Log", call_log):
        frappe.throw(_("Call log not found."))
    doc = frappe.get_doc("CRM Call Log", call_log)
    if doc.medium != "Teams":
        frappe.throw(_("Not a Teams call."))
    doc.status = status
    doc.end_time = now_datetime()
    if duration is not None:
        doc.duration = int(float(duration))
    if note:
        doc.add_comment("Comment", text=note)
    doc.save(ignore_permissions=True)
    return {"ok": True, "name": doc.name, "status": doc.status}
