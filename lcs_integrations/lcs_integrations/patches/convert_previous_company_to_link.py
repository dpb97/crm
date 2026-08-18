"""Turn Contact.previous_companies from free text into a CRM Organization
picker (single previous employer). The comma-split network-graph logic still
works (a single link value has no comma). Idempotent."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    # Small Text -> Link is not an allowed in-place fieldtype change, so drop the
    # old custom field and recreate it as a Link (existing free-text values in the
    # column are kept; only the control becomes a picker).
    existing = frappe.db.get_value(
        "Custom Field", {"dt": "Contact", "fieldname": "previous_companies"},
        ["name", "fieldtype"], as_dict=True,
    )
    if existing and existing.fieldtype != "Link":
        frappe.delete_doc("Custom Field", existing.name, ignore_permissions=True, force=True)
        frappe.db.commit()
    create_custom_fields(
        {
            "Contact": [
                {
                    "fieldname": "previous_companies",
                    "label": "Previous Company",
                    "fieldtype": "Link",
                    "options": "CRM Organization",
                    "description": "Former employer (for the network graph / career history).",
                    "insert_after": "company_name",
                }
            ]
        },
        update=True,
    )
