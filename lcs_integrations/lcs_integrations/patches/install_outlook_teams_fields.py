"""Custom fields for the Outlook contact + calendar sync and Teams notifications.

- Contact.graph_contact_id  — round-trip key for shared-mailbox push/pull.
- Event.graph_event_id      — round-trip key for calendar sync.

Idempotent — `create_custom_fields(update=True)` upserts.
"""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


CUSTOM_FIELDS: dict[str, list[dict]] = {
    "Contact": [
        {
            "fieldname": "graph_contact_id",
            "label": "Graph Contact ID",
            "fieldtype": "Data",
            "read_only": 1,
            "no_copy": 1,
            "description": (
                "Microsoft Graph contact ID in the shared sales mailbox. "
                "Set automatically by the LCS contacts push/pull jobs."
            ),
            "insert_after": "company_name",
        },
    ],
    "Event": [
        {
            "fieldname": "graph_event_id",
            "label": "Graph Event ID",
            "fieldtype": "Data",
            "read_only": 1,
            "no_copy": 1,
            "description": "Microsoft Graph event ID — set by the LCS calendar sync.",
            "insert_after": "subject",
        },
    ],
}


def execute() -> None:
    for fields in CUSTOM_FIELDS.values():
        for field_def in fields:
            field_def.setdefault("module", "LCS Integrations")
    create_custom_fields(CUSTOM_FIELDS, update=True)
    frappe.db.commit()
