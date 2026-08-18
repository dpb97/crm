"""Install the Sales-Meeting classification fields on LCS Project.

Mirrors the columns of the "Project & Sales Meeting" Excel protocol so the
offer pipeline (Angebote in Bearbeitung / Evidenz / Aufträge) can be run from
the CRM Sales Meeting page instead of the spreadsheet. Idempotent.
"""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


SOLUTION = "\n".join([
    "", "SB - Single Line", "SB - Double Line", "CC - Radial Crane",
    "CC - Parallel Crane", "CC - Luffing Tower", "QX - QXCrane", "WI - Winch", "Other",
])
SECTOR = "\n".join([
    "", "Hydro Power", "Dam Construction", "Mountain Construction",
    "Bridge Construction", "Pipeline", "Mining", "Other",
])
SALES_TYPE = "\n".join(["", "Rental", "Sale", "Service", "Mixed", "Rental or Sale"])
OFFER_STATUS = "\n".join([
    "", "Angebot", "Auftrag erwartet", "Auftrag", "Konkurrenz", "Fehler", "storniert", "gestoppt",
])

CUSTOM_FIELDS: dict[str, list[dict]] = {
    "LCS Project": [
        {"fieldname": "sm_section", "label": "Sales Meeting", "fieldtype": "Section Break",
         "insert_after": "richtpreis_impossible", "collapsible": 1},
        {"fieldname": "lcs_solution", "label": "Solution / Produkt", "fieldtype": "Select",
         "options": SOLUTION, "insert_after": "sm_section"},
        {"fieldname": "lcs_sector", "label": "Sector / Sektor", "fieldtype": "Select",
         "options": SECTOR, "insert_after": "lcs_solution"},
        {"fieldname": "lcs_sales_type", "label": "Sales Type", "fieldtype": "Select",
         "options": SALES_TYPE, "insert_after": "lcs_sector"},
        {"fieldname": "lcs_offer_status", "label": "Angebots-Status", "fieldtype": "Select",
         "options": OFFER_STATUS, "insert_after": "lcs_sales_type"},
        {"fieldname": "sm_col_break", "label": "", "fieldtype": "Column Break",
         "insert_after": "lcs_offer_status"},
        {"fieldname": "lcs_chance_lcs", "label": "Chance LCS (%)", "fieldtype": "Percent",
         "insert_after": "sm_col_break",
         "description": "Wahrscheinlichkeit, dass LCS den Auftrag bekommt."},
        {"fieldname": "lcs_chance_customer", "label": "Chance Projekt/Kunde (%)", "fieldtype": "Percent",
         "insert_after": "lcs_chance_lcs",
         "description": "Wahrscheinlichkeit, dass das Projekt überhaupt realisiert wird."},
        {"fieldname": "lcs_meeting_due", "label": "Fällig (Sales Meeting)", "fieldtype": "Data",
         "insert_after": "lcs_chance_customer",
         "description": "Freitext, z.B. KW10 oder ein Datum."},
        {"fieldname": "lcs_in_evidenz", "label": "In Evidenz (geparkt)", "fieldtype": "Check",
         "insert_after": "lcs_meeting_due"},
        {"fieldname": "lcs_rejection_reason", "label": "Grund Ablehnung", "fieldtype": "Small Text",
         "insert_after": "lcs_in_evidenz"},
    ],
}


def execute():
    create_custom_fields(CUSTOM_FIELDS, update=True)
