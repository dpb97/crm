"""Drop Custom Field rows for country / budget_range / decision_level /
expected_timeline on CRM Lead and CRM Deal.

These were introduced as Custom Fields by an earlier patch
(`install_pipeline_qualification_fields`) and have now been promoted
to native fields inside `crm_lead.json` / `crm_deal.json`. Frappe
errors out on the schema sync if both an own column and a Custom Field
of the same name exist on the same DocType — so the Custom Field rows
must go *before* the model sync runs.

Runs in `[pre_model_sync]` for that reason. Idempotent.
"""

from __future__ import annotations

import frappe


FIELDS = ("country", "budget_range", "decision_level", "expected_timeline")
DOCTYPES = ("CRM Lead", "CRM Deal")


def execute() -> None:
    deleted = 0
    for dt in DOCTYPES:
        for fn in FIELDS:
            name = frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": fn}, "name")
            if name:
                frappe.delete_doc("Custom Field", name, force=True, ignore_permissions=True)
                deleted += 1
                print(f"  - dropped Custom Field {dt}.{fn}")
    if deleted:
        frappe.db.commit()
    print(f"drop_lead_deal_qualification_custom_fields: removed {deleted} row(s)")
