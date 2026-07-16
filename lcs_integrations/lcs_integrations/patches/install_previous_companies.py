"""Add a 'Previous Companies' field to Contact for the network graph
(career history — "where did this person work before").
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields(
        {
            "Contact": [
                {
                    "fieldname": "previous_companies",
                    "label": "Previous Companies",
                    "fieldtype": "Small Text",
                    "description": "Comma-separated former employers (for the network graph).",
                    "insert_after": "company_name",
                }
            ]
        },
        ignore_validate=True,
    )
