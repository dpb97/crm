"""
Seed CRM Lead Source + CRM Lost Reason with common values used across LCS.

Idempotent — uses frappe.db.exists check before insert. Can be re-run safely.
"""

import frappe

LEAD_SOURCES = [
    "Direct",
    "Referral",
    "Website",
    "Trade Fair",
    "Partner",
    "Email Campaign",
    "Cold Call",
    "Existing Customer",
    "LinkedIn",
    "Other",
]

LOST_REASONS = [
    "Price too high",
    "Timing not right",
    "Competitor won",
    "Lost contact",
    "Budget cancelled",
    "Technical requirements not met",
    "No decision made",
    "Chose internal solution",
    "Other",
]


def execute():
    seed_doctype("CRM Lead Source", "source_name", LEAD_SOURCES)
    seed_doctype("CRM Lost Reason", "lost_reason", LOST_REASONS)


def seed_doctype(doctype, name_field, values):
    for value in values:
        if frappe.db.exists(doctype, value):
            continue
        doc = frappe.new_doc(doctype)
        # Different doctypes use different name fields; set the canonical one
        setattr(doc, name_field, value)
        # Frappe's autoname often falls back to the label field
        doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
    frappe.db.commit()
