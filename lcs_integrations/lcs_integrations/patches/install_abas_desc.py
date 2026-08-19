"""Add the abas project description (Sucherweiterung) as its own field on LCS
Project, so the readable description survives the rename to the abas Suchwort
(project code) and can be shown as its own list column. Idempotent."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields(
        {
            "LCS Project": [
                {
                    "fieldname": "lcs_abas_desc",
                    "label": "abas Bezeichnung",
                    "fieldtype": "Small Text",
                    "insert_after": "project_name",
                    "in_list_view": 0,
                    "translatable": 0,
                },
            ]
        },
        update=True,
    )
