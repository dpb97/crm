"""Add an `is_important` star flag to CRM Lead and CRM Deal (custom fields).

LCS Project carries the field natively in its DocType JSON; Leads and Deals
are upstream, so the flag is added as a custom field here.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields(
        {
            "CRM Lead": [
                {
                    "fieldname": "is_important",
                    "label": "Important",
                    "fieldtype": "Check",
                    "default": "0",
                    "insert_after": "status",
                }
            ],
            "CRM Deal": [
                {
                    "fieldname": "is_important",
                    "label": "Important",
                    "fieldtype": "Check",
                    "default": "0",
                    "insert_after": "status",
                }
            ],
        },
        ignore_validate=True,
    )
