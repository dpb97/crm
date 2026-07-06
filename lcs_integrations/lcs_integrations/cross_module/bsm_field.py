"""Optional BSM link on LCS Project.

"BSM Project" lives in the separate bsm app, which not every bench
running the CRM fork has installed. A hard Link field in
lcs_project.json fails DocType sync with LinkValidationError on benches
without it, so the field is created conditionally here instead
(same pattern as pilanda_sales' optional crm_deal link on Project).
"""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

BSM_CUSTOM_FIELDS = {
    "LCS Project": [
        {
            "fieldname": "bsm_project",
            "label": "BSM Project",
            "fieldtype": "Link",
            "options": "BSM Project",
            "insert_after": "erpnext_project",
            "read_only": 1,
        },
    ],
}


def ensure_bsm_field() -> None:
    """Idempotent: create the bsm_project link when the bsm app is present."""
    if not frappe.db.exists("DocType", "BSM Project"):
        return
    create_custom_fields(BSM_CUSTOM_FIELDS, ignore_validate=True)
