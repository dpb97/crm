"""Add an 'Archived' value to LCS Project.status so projects that are hidden in
the sales-meeting protocol can be archived without abusing 'Cancelled'
(which reads as lost/aborted). Idempotent via a Property Setter."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

OPTIONS = "Open\nActive\nOn Hold\nCompleted\nCancelled\nArchived"


def execute():
    make_property_setter(
        "LCS Project", "status", "options", OPTIONS, "Text",
        validate_fields_for_doctype=False,
    )
    frappe.clear_cache(doctype="LCS Project")
