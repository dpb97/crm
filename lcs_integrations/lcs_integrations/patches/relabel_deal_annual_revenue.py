"""Relabel CRM Deal `annual_revenue` -> "Geschätzter Umsatz".

On a Deal the native `annual_revenue` field (company annual revenue) is used as
the estimated deal/offer value, so "Jahresumsatz" is misleading. We keep the
field (data + currency binding intact) and only override its label via a
Property Setter, which propagates to the form, side panel, create dialog and
list column. Idempotent — make_property_setter updates the existing PS in place.
"""

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

_NEW_LABEL = "Geschätzter Umsatz"


def execute():
    make_property_setter(
        "CRM Deal",
        "annual_revenue",
        "label",
        _NEW_LABEL,
        "Data",
        validate_fields_for_doctype=False,
    )
    frappe.clear_cache(doctype="CRM Deal")
