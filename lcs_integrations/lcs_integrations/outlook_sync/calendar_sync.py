"""Inbound calendar sync: Outlook calendarView delta -> Frappe Event.

Runs once per `Outlook Mailbox Binding` (same row that drives mail delta).
Each Frappe Event is uniquely keyed by the Graph event id stored in the
Custom Field `graph_event_id` on Event.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import frappe

from .graph_client import GraphClient, GraphClientError


def _settings():
    return frappe.get_cached_doc("LCS Outlook Sync Settings")


def sync_all_calendars() -> None:
    s = _settings()
    if not s.enable_calendar_sync:
        return

    bindings = frappe.get_all(
        "Outlook Mailbox Binding",
        filters={"is_active": 1},
        fields=["name", "user", "graph_mailbox", "calendar_delta_token"],
    )
    for binding in bindings:
        try:
            sync_one_calendar(binding.name)
        except GraphClientError as exc:
            frappe.db.set_value("Outlook Mailbox Binding", binding.name, "last_error", str(exc))
            frappe.log_error(title="calendar_sync", message=str(exc))


def sync_one_calendar(binding_name: str) -> int:
    s = _settings()
    binding = frappe.get_doc("Outlook Mailbox Binding", binding_name)

    lookback = int(s.calendar_lookback_days or 7)
    lookahead = int(s.calendar_lookahead_days or 60)
    now = datetime.utcnow()
    start_iso = (now - timedelta(days=lookback)).isoformat() + "Z"
    end_iso = (now + timedelta(days=lookahead)).isoformat() + "Z"

    client = GraphClient()
    try:
        page = client.events_delta(
            binding.graph_mailbox,
            start_iso=start_iso,
            end_iso=end_iso,
            delta_link=binding.calendar_delta_token,
        )
    finally:
        client.close()

    upserts = 0
    for event in page.get("value", []):
        if _persist_event(binding.user, event):
            upserts += 1

    next_link = page.get("@odata.deltaLink") or page.get("@odata.nextLink")
    frappe.db.set_value(
        "Outlook Mailbox Binding",
        binding.name,
        {
            "calendar_delta_token": next_link,
            "last_calendar_sync": frappe.utils.now_datetime(),
            "last_error": None,
        },
    )
    return upserts


def _persist_event(user: str, event: dict[str, Any]) -> bool:
    graph_id = event.get("id")
    if not graph_id:
        return False

    # Soft-delete signalled by Graph as `@removed`
    if event.get("@removed"):
        existing = frappe.db.get_value("Event", {"graph_event_id": graph_id}, "name")
        if existing:
            frappe.delete_doc("Event", existing, ignore_permissions=True)
            return True
        return False

    subject = event.get("subject") or "(no subject)"
    starts_on = _parse_graph_dt(event.get("start"))
    ends_on = _parse_graph_dt(event.get("end"))
    body = (event.get("body") or {}).get("content") or ""

    existing_name = frappe.db.get_value("Event", {"graph_event_id": graph_id}, "name")
    if existing_name:
        ev = frappe.get_doc("Event", existing_name)
        ev.subject = subject
        ev.starts_on = starts_on
        ev.ends_on = ends_on
        ev.description = body
        _link_event_to_crm(ev, event)
        ev.save(ignore_permissions=True)
    else:
        ev = frappe.get_doc(
            {
                "doctype": "Event",
                "subject": subject,
                "starts_on": starts_on,
                "ends_on": ends_on,
                "description": body,
                "event_category": "Meeting",
                "event_type": "Private",
                "owner": user,
                "graph_event_id": graph_id,
            }
        )
        _link_event_to_crm(ev, event)
        ev.insert(ignore_permissions=True)
    return True


def _attendee_emails(event: dict[str, Any]) -> list[str]:
    """All participant addresses of a Graph event (attendees + organizer)."""
    out = []
    for a in event.get("attendees") or []:
        addr = ((a.get("emailAddress") or {}).get("address") or "").strip().lower()
        if addr:
            out.append(addr)
    org = (((event.get("organizer") or {}).get("emailAddress") or {}).get("address") or "").strip().lower()
    if org:
        out.append(org)
    return out


def _link_event_to_crm(ev, event: dict[str, Any]) -> None:
    """Attach the Event to the CRM record its participants belong to, so it
    shows up in the Events tab on the Lead/Deal page.

    Match order per attendee address: open CRM Lead by email, CRM Deal by
    primary-contact email, then Contact -> a deal that contact is linked
    to. An existing reference is never overwritten (users may relink
    manually in the desk).
    """
    if ev.get("reference_docname"):
        return
    for addr in _attendee_emails(event):
        lead = frappe.db.get_value("CRM Lead", {"email": addr, "converted": 0}, "name")
        if lead:
            ev.reference_doctype, ev.reference_docname = "CRM Lead", lead
            return
        deal = frappe.db.get_value("CRM Deal", {"email": addr}, "name")
        if deal:
            ev.reference_doctype, ev.reference_docname = "CRM Deal", deal
            return
        contact = frappe.db.get_value("Contact Email", {"email_id": addr}, "parent")
        if contact:
            deal = frappe.db.get_value(
                "CRM Contacts", {"contact": contact, "parenttype": "CRM Deal"}, "parent"
            )
            if deal:
                ev.reference_doctype, ev.reference_docname = "CRM Deal", deal
                return


def _parse_graph_dt(node: dict[str, Any] | None) -> str | None:
    """Graph returns `{ dateTime: "...", timeZone: "..." }` — Frappe stores naive UTC strings."""
    if not node:
        return None
    raw = node.get("dateTime")
    if not raw:
        return None
    # Strip fractional seconds Graph sometimes emits, normalise to space-separated.
    return raw.replace("T", " ").split(".")[0]
