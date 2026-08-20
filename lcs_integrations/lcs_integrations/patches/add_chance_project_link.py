"""Chance → Project (instead of Chance → Lead): add a link field lcs_project on
LCS Chance and a 'Vertriebsprojekt' status value. Idempotent."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

STATUS = "Neu\nIn Bearbeitung\nRelevant\nKontakt aufgenommen\nVertriebsprojekt\nKeine Chance"


def execute():
    create_custom_fields(
        {
            "LCS Chance": [
                {
                    "fieldname": "lcs_project",
                    "label": "Sales Project",
                    "fieldtype": "Link",
                    "options": "LCS Project",
                    "insert_after": "crm_lead",
                    "read_only": 1,
                },
            ]
        },
        update=True,
    )
    make_property_setter("LCS Chance", "status", "options", STATUS, "Text",
                         validate_fields_for_doctype=False)
    frappe.clear_cache(doctype="LCS Chance")
