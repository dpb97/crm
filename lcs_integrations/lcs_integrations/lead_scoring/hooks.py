"""Doc-event hook that recomputes the lead score on every update."""

from __future__ import annotations

from typing import Any

import frappe

from .engine import score


_FLAG = "lcs_scoring_in_progress"


def recompute_score(doc: Any, method: str | None = None) -> None:
    if frappe.flags.get(_FLAG):
        return
    rules = frappe.get_all(
        "Lead Scoring Rule",
        filters={"active": 1},
        fields=["field_name", "operator", "value", "score_delta", "priority", "active"],
    )
    new_score = score(doc.as_dict(), rules)
    if doc.get("lcs_score") == new_score:
        return
    frappe.flags[_FLAG] = True
    try:
        # Target ERPNext's `Lead` DocType (frappe/crm's `CRM Lead` is not
        # installed on this bench).
        frappe.db.set_value("Lead", doc.name, "lcs_score", new_score, update_modified=False)
    finally:
        frappe.flags[_FLAG] = False
