"""Store the auto-created SharePoint page URL on the LCS Project. Idempotent."""

from __future__ import annotations

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields(
        {
            "LCS Project": [
                {
                    "fieldname": "lcs_sharepoint_url",
                    "label": "SharePoint",
                    "fieldtype": "Data",
                    "options": "URL",
                    "read_only": 1,
                    "insert_after": "project_name",
                    "translatable": 0,
                },
            ]
        },
        update=True,
    )
