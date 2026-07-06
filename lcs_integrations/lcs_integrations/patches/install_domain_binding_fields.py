"""Custom field for domain-based contact binding.

- CRM Organization.email_domain — the customer's primary mail domain
  (e.g. "kunde.de"). Contacts whose email shares this domain are linked
  to the organization by the LCS domain-binding service.

Idempotent — `create_custom_fields(update=True)` upserts.
"""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


CUSTOM_FIELDS: dict[str, list[dict]] = {
    "CRM Organization": [
        {
            "fieldname": "email_domain",
            "label": "Email Domain",
            "fieldtype": "Data",
            "description": (
                "Primary mail domain of this customer (e.g. kunde.de). "
                "Contacts and emails matching this domain are auto-linked "
                "to this organization and its active project."
            ),
            "insert_after": "website",
        },
    ],
}


def execute() -> None:
    for fields in CUSTOM_FIELDS.values():
        for field_def in fields:
            field_def.setdefault("module", "LCS Integrations")
    create_custom_fields(CUSTOM_FIELDS, update=True)
    frappe.db.commit()
