"""Add an academic/honorific title field (lcs_title) to Contact and seed the
usual German salutations so the Contact "Anrede" picker is no longer empty
("Keine Ergebnisse gefunden"). Idempotent."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Usual salutations (Anrede) — the honorific/academic title is a separate field.
SALUTATIONS = ["Herr", "Frau", "Divers", "Firma", "Familie"]


def execute():
    create_custom_fields(
        {
            "Contact": [
                {
                    "fieldname": "lcs_title",
                    "label": "Titel",
                    "fieldtype": "Data",
                    "insert_after": "salutation",
                    "translatable": 0,
                    "description": "Akademischer/beruflicher Titel (z. B. Dr., Mag., DI, Prof.)",
                },
            ]
        },
        update=True,
    )

    for s in SALUTATIONS:
        if not frappe.db.exists("Salutation", s):
            frappe.get_doc({"doctype": "Salutation", "salutation": s}).insert(
                ignore_permissions=True
            )
