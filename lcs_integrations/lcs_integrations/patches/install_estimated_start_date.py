"""Add an 'Expected Start Date' to CRM Lead and CRM Deal (custom fields).

LCS Project carries the field natively in its DocType JSON; Leads and Deals
are upstream, so the field is added as a custom field here.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    field = {
        "fieldname": "expected_start_date",
        "label": "Expected Start Date",
        "fieldtype": "Date",
        "insert_after": "status",
    }
    create_custom_fields(
        {"CRM Lead": [dict(field)], "CRM Deal": [dict(field)]},
        ignore_validate=True,
    )
