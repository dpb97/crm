"""Compat guard against third-party apps bending core doctypes we sync to.

`erpnext_enhancements` (Sapphire Fountains) ships Property Setter fixtures
that override `Customer.customer_type` options from the ERPNext standard
(Company/Individual/Partnership) to Commercial/Residential/Partnership.
Fixtures re-import on EVERY `bench migrate`, so a one-time delete does not
stick — and with the override in place our CRM Organization -> Customer
sync (which writes the standard value "Company") fails validation on every
organization insert/update.

This guard runs as `after_migrate` (fixtures sync earlier in the same
migrate), removing any Property Setter on Customer.customer_type so the
field stays ERPNext standard. LCS owns this decision: do not re-add
setters on this field — extend via a separate custom field instead.
"""

from __future__ import annotations

import frappe

GUARDED = [
    # (doc_type, field_name) pairs that must stay ERPNext standard
    ("Customer", "customer_type"),
]


def remove_conflicting_property_setters() -> None:
    """after_migrate hook — idempotent, logs what it removes."""
    removed = []
    for doc_type, field_name in GUARDED:
        names = frappe.get_all(
            "Property Setter",
            filters={"doc_type": doc_type, "field_name": field_name},
            pluck="name",
        )
        for name in names:
            frappe.delete_doc(
                "Property Setter", name,
                ignore_permissions=True, force=True, ignore_missing=True,
            )
            removed.append(name)
        if names:
            frappe.clear_cache(doctype=doc_type)
    if removed:
        frappe.db.commit()
        frappe.logger("lcs_integrations").info(
            f"compat guard removed conflicting property setters: {removed}"
        )
        print(f"lcs_integrations compat guard: removed {removed}")
