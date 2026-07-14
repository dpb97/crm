"""Backfill LCS Project.currency from the linked CRM Deal.

The project now carries its own currency (deal currency) so the pricing stages
render in CHF/USD/... instead of always EUR. Existing projects predate the
field — copy it from the linked deal, defaulting to EUR. Idempotent: skips
projects that already have a currency.
"""

import frappe


def execute():
    for p in frappe.get_all("LCS Project", fields=["name", "deal", "currency"]):
        if p.currency:
            continue
        cur = frappe.db.get_value("CRM Deal", p.deal, "currency") if p.deal else None
        frappe.db.set_value(
            "LCS Project", p.name, "currency", cur or "EUR", update_modified=False
        )
