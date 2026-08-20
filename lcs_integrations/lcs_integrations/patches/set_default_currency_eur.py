"""Pin the CRM default currency to EUR and relabel stray INR values.

An empty System Settings currency fell back to INR, so amounts rendered with the
₹ symbol instead of €, and all existing LCS Projects were stamped currency=INR
(their amounts are EUR values, only mislabelled). Sets the system default to EUR
and relabels INR/empty LCS Project currencies to EUR. Idempotent — never touches
a record that already carries a real (non-INR) currency.
"""

from __future__ import annotations

import frappe

RELABEL_DOCTYPES = ["LCS Project", "LCS Offer"]


def execute():
    # System-wide default → EUR (both the Singles field and the global default
    # that frappe.db.get_default('currency') reads).
    if (frappe.db.get_single_value("System Settings", "currency") or "") != "EUR":
        frappe.db.set_single_value("System Settings", "currency", "EUR")
    frappe.db.set_default("currency", "EUR")
    if frappe.db.exists("Currency", "EUR"):
        frappe.db.set_value("Currency", "EUR", "enabled", 1)

    # Relabel the stray INR/empty currency on existing records (values are EUR).
    for dt in RELABEL_DOCTYPES:
        if not frappe.db.exists("DocType", dt):
            continue
        meta = frappe.get_meta(dt)
        if not any(f.fieldname == "currency" for f in meta.fields):
            continue
        for row in frappe.get_all(dt, fields=["name", "currency"]):
            if (row.currency or "") in ("", "INR"):
                frappe.db.set_value(dt, row.name, "currency", "EUR", update_modified=False)
