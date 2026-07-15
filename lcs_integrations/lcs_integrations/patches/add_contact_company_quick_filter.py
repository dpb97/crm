"""Make Firma (company_name) a quick filter on the Contacts (Personen) list.

Quick filters come from a CRM Global Settings "Quick Filters" entry per doctype,
falling back to the doctype's in_standard_filter fields. Ensure company_name is
present either way so users can filter contacts by their organisation. Idempotent.
"""

import json

import frappe


def execute():
    name = frappe.db.exists(
        "CRM Global Settings", {"dt": "Contact", "type": "Quick Filters"}
    )
    if name:
        doc = frappe.get_doc("CRM Global Settings", name)
        filters = json.loads(doc.json or "[]")
        if "company_name" not in filters:
            filters.append("company_name")
            doc.json = json.dumps(filters)
            doc.save(ignore_permissions=True)
    else:
        # No explicit config yet — mark the field so the default fallback picks
        # it up.
        from frappe.custom.doctype.property_setter.property_setter import (
            make_property_setter,
        )

        make_property_setter(
            "Contact", "company_name", "in_standard_filter", 1, "Check",
            validate_fields_for_doctype=False,
        )
    frappe.clear_cache(doctype="Contact")
