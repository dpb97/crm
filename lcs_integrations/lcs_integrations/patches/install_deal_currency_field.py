"""Expose the CRM Deal `currency` field in the create dialog + side panel.

`currency` exists on CRM Deal natively (with `annual_revenue` bound to it), but
it ships absent from every `CRM Fields Layout`, so users can't pick a deal's
target currency and everything falls back to the system default. This inserts
`currency` right before `annual_revenue` in the Quick Entry (create dialog) and
Side Panel layouts. Idempotent — skips a layout that already has the field.
"""

import json

import frappe

_LAYOUT_TYPES = ["Quick Entry", "Side Panel"]
_ANCHOR = "annual_revenue"
_FIELD = "currency"


def _insert(layout: list) -> bool:
    # Already present anywhere? -> nothing to do.
    for section in layout:
        for column in section.get("columns", []):
            if _FIELD in column.get("fields", []):
                return False
    # Insert before the anchor in the first column that holds it.
    for section in layout:
        for column in section.get("columns", []):
            fields = column.get("fields", [])
            if _ANCHOR in fields:
                fields.insert(fields.index(_ANCHOR), _FIELD)
                column["fields"] = fields
                return True
    return False


def execute():
    for layout_type in _LAYOUT_TYPES:
        name = frappe.db.get_value(
            "CRM Fields Layout", {"dt": "CRM Deal", "type": layout_type}, "name"
        )
        if not name:
            continue
        doc = frappe.get_doc("CRM Fields Layout", name)
        try:
            layout = json.loads(doc.layout or "[]")
        except (TypeError, ValueError):
            continue
        if _insert(layout):
            doc.layout = json.dumps(layout)
            doc.save(ignore_permissions=True)
