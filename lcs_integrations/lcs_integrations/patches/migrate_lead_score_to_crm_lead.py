"""Move `lcs_score` from ERPNext `Lead` to FrappeCRM `CRM Lead`.

The score was originally attached to the ERPNext Lead DocType, but the
on_update hook fires on CRM Lead (where sales actually edits leads),
so the score was never recomputed in practice. Drop the orphan field
on Lead and ensure the field exists on CRM Lead.

Idempotent — safe to re-run.
"""

from __future__ import annotations

import frappe


def execute() -> None:
    cf_name = frappe.db.get_value(
        "Custom Field", {"dt": "Lead", "fieldname": "lcs_score"}
    )
    if cf_name:
        try:
            frappe.delete_doc(
                "Custom Field", cf_name, ignore_permissions=True, force=1
            )
        except Exception as e:
            frappe.log_error(
                f"Could not drop Lead.lcs_score: {e}",
                "migrate_lead_score_to_crm_lead",
            )

    from lcs_integrations.patches.v1_0.install_custom_fields import execute as install
    install()

    frappe.db.commit()
