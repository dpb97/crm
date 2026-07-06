"""Custom fields for owner-only contact visibility until release.

A Contact stays visible only to its creator (owner) until `lcs_released`
is set — then it becomes visible to everyone with Contact read access.
See lcs_integrations.visibility.contact_visibility.

Existing contacts are grandfathered to released=1 so the install does not
retroactively hide the whole address book.

Idempotent — `create_custom_fields(update=True)` upserts; the grandfather
update only flips NULL/0 rows that predate the field.
"""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


CUSTOM_FIELDS: dict[str, list[dict]] = {
    "Contact": [
        {
            "fieldname": "lcs_released",
            "label": "Released",
            "fieldtype": "Check",
            "default": "0",
            "read_only": 1,
            "description": (
                "Until released, this contact is visible only to its creator. "
                "Release it from the CRM to share it with the team."
            ),
            "insert_after": "company_name",
        },
        {
            "fieldname": "lcs_released_by",
            "label": "Released By",
            "fieldtype": "Link",
            "options": "User",
            "read_only": 1,
            "no_copy": 1,
            "insert_after": "lcs_released",
        },
        {
            "fieldname": "lcs_released_on",
            "label": "Released On",
            "fieldtype": "Datetime",
            "read_only": 1,
            "no_copy": 1,
            "insert_after": "lcs_released_by",
        },
    ],
}


def execute() -> None:
    is_fresh_install = not frappe.db.has_column("Contact", "lcs_released")

    for fields in CUSTOM_FIELDS.values():
        for field_def in fields:
            field_def.setdefault("module", "LCS Integrations")
    create_custom_fields(CUSTOM_FIELDS, update=True)

    # Grandfather every pre-existing contact so we never hide the address
    # book that was visible before this feature shipped.
    if is_fresh_install:
        frappe.db.sql("UPDATE `tabContact` SET lcs_released = 1")
    frappe.db.commit()
