"""Install Custom Fields used by the LCS adaptations.

Idempotent — Frappe's `create_custom_fields` upserts when called with
`update=True`. Targets ERPNext DocTypes (Lead / Customer / Quotation /
Sales Order / Contact); the frappe/crm DocTypes are not part of this stack.
"""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


CUSTOM_FIELDS: dict[str, list[dict]] = {
    "Lead": [
        {
            "fieldname": "lcs_source",
            "label": "LCS Source",
            "fieldtype": "Select",
            "options": "\nFair\nWebsite\nCold Call\nReferral\nOther",
            "insert_after": "source",
        },
        {
            "fieldname": "lcs_score",
            "label": "Lead Score",
            "fieldtype": "Int",
            "read_only": 1,
            "insert_after": "lcs_source",
        },
    ],
    "Customer": [
        {
            "fieldname": "abas_id",
            "label": "abas Customer ID",
            "fieldtype": "Data",
            "unique": 0,
            "read_only": 1,
            "insert_after": "customer_name",
        },
    ],
    "Quotation": [
        {
            "fieldname": "abas_quotation_no",
            "label": "abas Quotation #",
            "fieldtype": "Data",
            "read_only": 1,
            "insert_after": "status",
        },
    ],
    "Sales Order": [
        {
            "fieldname": "abas_order_no",
            "label": "abas Order #",
            "fieldtype": "Data",
            "read_only": 1,
            "insert_after": "status",
        },
        # `delivery_status` already exists as an ERPNext core field with
        # ERPNext semantics (Not Delivered/Fully Delivered/...). The LCS
        # fields carry abas's own lifecycle and are namespaced with `lcs_`
        # so they never collide with core ERPNext fields.
        {
            "fieldname": "lcs_delivery_status",
            "label": "LCS Delivery Status (abas)",
            "fieldtype": "Select",
            "options": "\nPending\nPlanned\nShipped\nDelivered",
            "read_only": 1,
            "insert_after": "abas_order_no",
        },
        {
            "fieldname": "lcs_planned_ship_date",
            "label": "Planned Ship Date (abas)",
            "fieldtype": "Date",
            "read_only": 1,
            "insert_after": "lcs_delivery_status",
        },
        {
            "fieldname": "lcs_real_revenue",
            "label": "Real Revenue (abas)",
            "fieldtype": "Currency",
            "read_only": 1,
            "insert_after": "lcs_planned_ship_date",
        },
    ],
    "Contact": [
        {
            "fieldname": "abas_contact_id",
            "label": "abas Contact ID",
            "fieldtype": "Data",
            "read_only": 1,
            "insert_after": "company_name",
        },
    ],
}


def execute() -> None:
    # `update=True` makes the call idempotent on existing sites.
    create_custom_fields(CUSTOM_FIELDS, update=True)
    frappe.db.commit()
