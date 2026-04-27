"""Install Custom Fields used by the LCS adaptations.

Idempotent — Frappe's `create_custom_fields` upserts when called with
`update=True`. Targets ERPNext DocTypes (Lead / Customer / Quotation /
Sales Order / Contact) and CRM Organization to wire the cross-module
links used by LCS Integrations.
"""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


CUSTOM_FIELDS: dict[str, list[dict]] = {
    "Lead": [
        {
            "fieldname": "lcs_score",
            "label": "Lead Score",
            "fieldtype": "Int",
            "read_only": 1,
            "insert_after": "source",
        },
    ],
    "CRM Organization": [
        {
            "fieldname": "erpnext_customer",
            "label": "ERPNext Customer",
            "fieldtype": "Link",
            "options": "Customer",
            "read_only": 1,
            "insert_after": "organization_name",
        },
    ],
    "CRM Deal": [
        {
            "fieldname": "erpnext_customer",
            "label": "ERPNext Customer",
            "fieldtype": "Link",
            "options": "Customer",
            "read_only": 1,
            "insert_after": "organization",
        },
        {
            "fieldname": "sales_manager",
            "label": "Sales Manager",
            "fieldtype": "Link",
            "options": "User",
            "description": "Propagated from the linked LCS Project (single source of truth).",
            "insert_after": "deal_owner",
        },
    ],
    "CRM Lead": [
        {
            "fieldname": "erpnext_customer",
            "label": "ERPNext Customer",
            "fieldtype": "Link",
            "options": "Customer",
            "read_only": 1,
            "insert_after": "organization",
        },
        {
            "fieldname": "sales_manager",
            "label": "Sales Manager",
            "fieldtype": "Link",
            "options": "User",
            "description": "Propagated from the linked LCS Project (single source of truth).",
            "insert_after": "lead_owner",
        },
    ],
    "Sales Order": [
        {
            "fieldname": "lcs_project",
            "label": "LCS Project",
            "fieldtype": "Link",
            "options": "LCS Project",
            "insert_after": "status",
        },
    ],
    "Quotation": [
        {
            "fieldname": "lcs_offer",
            "label": "LCS Offer",
            "fieldtype": "Link",
            "options": "LCS Offer",
            "read_only": 1,
            "insert_after": "status",
        },
    ],
    "BSM Project": [
        {
            "fieldname": "lcs_project",
            "label": "LCS Project",
            "fieldtype": "Link",
            "options": "LCS Project",
            "insert_after": "project_name",
        },
        {
            "fieldname": "sales_order",
            "label": "Sales Order",
            "fieldtype": "Link",
            "options": "Sales Order",
            "read_only": 1,
            "insert_after": "lcs_project",
        },
    ],
    # Reverse link from ERPNext Project back to LCS Project — execution
    # data (tasks, time logs, costing) lives in ERPNext while sales
    # data (phase, pricing, matrix) lives in LCS Project. The link
    # makes both sides navigable.
    "Project": [
        {
            "fieldname": "lcs_project",
            "label": "LCS Project",
            "fieldtype": "Link",
            "options": "LCS Project",
            "insert_after": "project_name",
            "description": "Sales-side project record carrying phase, pricing, opportunity matrix.",
        },
    ],
}


def execute() -> None:
    """Idempotent.

    Stamps every field with `module = "LCS Integrations"` so the
    Frappe fixtures export hook (filters by module) finds them, and
    so uninstalling the app cleanly removes them. Without this stamp
    the fields exist orphaned with module=NULL — a real cleanup
    smell that hides them from the fixtures pipeline.
    """
    for field_list in CUSTOM_FIELDS.values():
        for field_def in field_list:
            field_def.setdefault("module", "LCS Integrations")
    create_custom_fields(CUSTOM_FIELDS, update=True)

    # Heal pre-existing rows that were inserted with module=NULL by
    # earlier runs of this patch. Same set of fieldnames; we just stamp
    # the module on existing rows.
    healed = 0
    for dt, fields in CUSTOM_FIELDS.items():
        for f in fields:
            row = frappe.db.get_value(
                "Custom Field",
                {"dt": dt, "fieldname": f["fieldname"]},
                ["name", "module"],
                as_dict=True,
            )
            if row and not row.module:
                frappe.db.set_value("Custom Field", row.name, "module", "LCS Integrations")
                healed += 1
    if healed:
        print(f"install_custom_fields: stamped module on {healed} legacy field row(s)")

    frappe.db.commit()
