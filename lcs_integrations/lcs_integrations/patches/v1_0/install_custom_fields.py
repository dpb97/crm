"""Install Custom Fields used by the LCS adaptations.

Idempotent — Frappe's `create_custom_fields` upserts when called with
`update=True`. Targets ERPNext DocTypes (Customer / Quotation / Sales
Order / Contact) and FrappeCRM DocTypes (CRM Lead / CRM Deal / CRM
Organization) to wire the cross-module links used by LCS Integrations.
"""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


CUSTOM_FIELDS: dict[str, list[dict]] = {
    "CRM Organization": [
        {
            "fieldname": "erpnext_customer",
            "label": "ERPNext Customer",
            "fieldtype": "Link",
            "options": "Customer",
            "read_only": 1,
            "insert_after": "organization_name",
        },
    ],
    "CRM Deal": [
        {
            "fieldname": "erpnext_customer",
            "label": "ERPNext Customer",
            "fieldtype": "Link",
            "options": "Customer",
            "read_only": 1,
            "insert_after": "organization",
        },
        {
            "fieldname": "sales_manager",
            "label": "Sales Manager",
            "fieldtype": "Link",
            "options": "User",
            "description": "Propagated from the linked LCS Project (single source of truth). Auto-filled from market-split territory on insert.",
            "insert_after": "deal_owner",
        },
    ],
    "CRM Lead": [
        {
            "fieldname": "erpnext_customer",
            "label": "ERPNext Customer",
            "fieldtype": "Link",
            "options": "Customer",
            "read_only": 1,
            "insert_after": "organization",
        },
        {
            "fieldname": "sales_manager",
            "label": "Sales Manager",
            "fieldtype": "Link",
            "options": "User",
            "description": "Propagated from the linked LCS Project (single source of truth). Auto-filled from market-split territory on insert.",
            "insert_after": "lead_owner",
        },
        {
            "fieldname": "lcs_score",
            "label": "Lead Score",
            "fieldtype": "Int",
            "read_only": 1,
            "insert_after": "sales_manager",
        },
    ],
    "Sales Order": [
        {
            "fieldname": "lcs_project",
            "label": "LCS Project",
            "fieldtype": "Link",
            "options": "LCS Project",
            "insert_after": "status",
        },
    ],
    "Quotation": [
        {
            "fieldname": "lcs_offer",
            "label": "LCS Offer",
            "fieldtype": "Link",
            "options": "LCS Offer",
            "read_only": 1,
            "insert_after": "status",
        },
    ],
    "BSM Project": [
        {
            "fieldname": "lcs_project",
            "label": "LCS Project",
            "fieldtype": "Link",
            "options": "LCS Project",
            "insert_after": "project_name",
        },
        {
            "fieldname": "sales_order",
            "label": "Sales Order",
            "fieldtype": "Link",
            "options": "Sales Order",
            "read_only": 1,
            "insert_after": "lcs_project",
        },
    ],
    # Reverse link from ERPNext Project back to LCS Project — execution
    # data (tasks, time logs, costing) lives in ERPNext while sales
    # data (phase, pricing, matrix) lives in LCS Project. The link
    # makes both sides navigable.
    "Project": [
        {
            "fieldname": "lcs_project",
            "label": "LCS Project",
            "fieldtype": "Link",
            "options": "LCS Project",
            "insert_after": "project_name",
            "description": "Sales-side project record carrying phase, pricing, opportunity matrix.",
        },
    ],
    # W-01..W-06 Network follow-up ride on Frappe ToDo: we add the LCS
    # taxonomy fields directly so the existing reminder / scheduler
    # machinery stays as-is. lcs_kind discriminates a network follow-up
    # from a regular task; lcs_reason carries the short context shown
    # when the reminder fires.
    # Sales hierarchy lives on the User itself so role-based scoping
    # for follow-ups, dashboards and access profiles all share one
    # source of truth. Manually maintained.
    "User": [
        {
            "fieldname": "sales_manager",
            "label": "Sales Manager",
            "fieldtype": "Link",
            "options": "User",
            "description": "This user reports to that sales manager. Used for LCS follow-up visibility and team dashboards.",
            "insert_after": "username",
        },
    ],
    "ToDo": [
        {
            "fieldname": "lcs_kind",
            "label": "LCS Kind",
            "fieldtype": "Select",
            "options": "\nFollow-up\nTask",
            "default": "",
            "insert_after": "status",
        },
        {
            "fieldname": "lcs_reason",
            "label": "LCS Reason",
            "fieldtype": "Small Text",
            "description": "Context shown when the reminder fires (e.g. 'Met at Bauma 2026', 'Project paused, recheck Q3').",
            "insert_after": "lcs_kind",
        },
        {
            "fieldname": "lcs_visible_to_manager",
            "label": "Visible to Sales Manager",
            "fieldtype": "Check",
            "default": "1",
            "description": "Sales manager of the assigned user sees this follow-up. Other sales reps do not.",
            "insert_after": "lcs_reason",
        },
        {
            "fieldname": "lcs_notify_email",
            "label": "Notify by Email",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "lcs_visible_to_manager",
        },
        {
            "fieldname": "lcs_notify_teams",
            "label": "Notify in Teams",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "lcs_notify_email",
        },
        {
            "fieldname": "lcs_notify_push",
            "label": "Notify by Push (Mobile)",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "lcs_notify_teams",
        },
        {
            "fieldname": "lcs_fired_at",
            "label": "LCS Reminder Fired At",
            "fieldtype": "Datetime",
            "read_only": 1,
            "description": "Timestamp the scheduler dispatched the reminder. Empty means due / pending.",
            "insert_after": "lcs_notify_push",
        },
    ],
}


def execute() -> None:
    """Idempotent.

    Stamps every field with `module = "LCS Integrations"` so the
    Frappe fixtures export hook (filters by module) finds them, and
    so uninstalling the app cleanly removes them. Without this stamp
    the fields exist orphaned with module=NULL — a real cleanup
    smell that hides them from the fixtures pipeline.
    """
    for field_list in CUSTOM_FIELDS.values():
        for field_def in field_list:
            field_def.setdefault("module", "LCS Integrations")

    # Optional integrations: skip target doctypes whose app isn't
    # installed on this bench (e.g. BSM Project without the bsm app) —
    # a Custom Field row on a missing doctype fails link validation.
    present = {
        dt: fields
        for dt, fields in CUSTOM_FIELDS.items()
        if frappe.db.exists("DocType", dt)
    }
    skipped = set(CUSTOM_FIELDS) - set(present)
    if skipped:
        print(f"install_custom_fields: skipping absent doctypes {sorted(skipped)}")
    create_custom_fields(present, update=True)

    # Heal pre-existing rows that were inserted with module=NULL by
    # earlier runs of this patch. Same set of fieldnames; we just stamp
    # the module on existing rows.
    healed = 0
    for dt, fields in present.items():
        for f in fields:
            row = frappe.db.get_value(
                "Custom Field",
                {"dt": dt, "fieldname": f["fieldname"]},
                ["name", "module"],
                as_dict=True,
            )
            if row and not row.module:
                frappe.db.set_value("Custom Field", row.name, "module", "LCS Integrations")
                healed += 1
    if healed:
        print(f"install_custom_fields: stamped module on {healed} legacy field row(s)")

    frappe.db.commit()
