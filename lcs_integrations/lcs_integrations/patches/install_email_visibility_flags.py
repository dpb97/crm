"""Add the e-mail visibility flags (lcs_shared, lcs_internal) to Communication
and backfill them for existing synced mail.

lcs_shared   = project ref in subject OR crm@lcs-group.com in CC → visible to all
lcs_internal = internal-to-internal (sender + all recipients @lcs-group.com)

The visibility filter then hides internal-to-internal mail that is not shared,
and keeps non-shared mail private to its mailbox owner. Idempotent. CC was not
stored on older imports, so the backfill evaluates crm-in-cc from the stored
recipients only — new mail carries the exact CC.
"""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from lcs_integrations.visibility import email_visibility


def execute():
    create_custom_fields(
        {
            "Communication": [
                {
                    "fieldname": "lcs_shared",
                    "label": "LCS Shared",
                    "fieldtype": "Check",
                    "insert_after": "user",
                    "default": "0",
                    "no_copy": 1,
                },
                {
                    "fieldname": "lcs_internal",
                    "label": "LCS Internal",
                    "fieldtype": "Check",
                    "insert_after": "lcs_shared",
                    "default": "0",
                    "no_copy": 1,
                },
            ]
        },
        update=True,
    )

    rows = frappe.get_all(
        "Communication",
        filters={"communication_medium": "Email"},
        fields=["name", "sender", "subject", "recipients", "cc", "user"],
        limit=0,
    )
    for i, r in enumerate(rows, 1):
        if not (r.get("user") or "").strip():
            # Not a mailbox-owned mail (manual / other source) → keep it visible.
            shared, internal = 1, 0
        else:
            flags = email_visibility.compute_flags(
                r.get("sender") or "", r.get("subject"), r.get("recipients"), r.get("cc")
            )
            shared, internal = flags["lcs_shared"], flags["lcs_internal"]
        frappe.db.set_value(
            "Communication", r.name,
            {"lcs_shared": shared, "lcs_internal": internal},
            update_modified=False,
        )
        if i % 2000 == 0:
            frappe.db.commit()
    frappe.db.commit()
