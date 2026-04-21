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
}


def execute() -> None:
    # `update=True` makes the call idempotent on existing sites.
    create_custom_fields(CUSTOM_FIELDS, update=True)
    frappe.db.commit()
