"""Add the Opportunity-Matrix fields (5 dimensions, 0-100) to LCS Project, so the
sales rep can estimate a project's chance in the docked project inspector radar
(same 5 axes as the Pilot chance rating). Idempotent."""

from __future__ import annotations

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    fields = [
        ("technical_fit", "Technical Fit"),
        ("commercial_fit", "Commercial Fit"),
        ("relationship_strength", "Relationship"),
        ("competition_level", "Competition"),
        ("strategic_importance", "Strategic Value"),
    ]
    prev = "is_important"
    defs = []
    for fn, label in fields:
        defs.append({
            "fieldname": fn,
            "label": label,
            "fieldtype": "Int",
            "insert_after": prev,
            "description": "Opportunity matrix (0-100)",
            "translatable": 0,
        })
        prev = fn
    create_custom_fields({"LCS Project": defs}, update=True)
