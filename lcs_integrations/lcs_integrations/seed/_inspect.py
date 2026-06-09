"""Tiny inspection helper — for `bench execute` only, prints to stderr."""

from __future__ import annotations

import sys

import frappe


def install_procurement_feed_field() -> None:
    """Install the missing `custom_material_request_feed` HTML field.

    This is a hot-fix for `erpnext_enhancements` — the app references the
    field as the anchor for the Procurement buttons section but never
    actually creates it. The Vue procurement-tracker widget (loaded by
    project_enhancements.js) renders into this field's wrapper.

    Idempotent — `create_custom_fields(update=True)` upserts.
    """
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    create_custom_fields(
        {
            "Project": [
                {
                    "fieldname": "custom_material_request_feed",
                    "label": "Procurement Tracker",
                    "fieldtype": "HTML",
                    "insert_after": "total_consumed_material_cost",
                    "description": "Container for the Vue-rendered procurement tracker (erpnext_enhancements).",
                },
            ]
        },
        update=True,
    )
    frappe.db.commit()
    print("custom_material_request_feed installed on Project", file=sys.stderr)


def diag_project_custom_fields() -> None:
    """Quick scan: which Project custom fields exist + which patches ran?"""
    cf_rows = frappe.db.sql(
        """SELECT fieldname, fieldtype, label, insert_after
           FROM `tabCustom Field`
           WHERE dt='Project'
             AND (fieldname LIKE '%material%' OR fieldname LIKE '%procurement%' OR fieldname LIKE '%feed%')
           ORDER BY fieldname""",
        as_dict=True,
    )
    print(f"Project custom fields ({len(cf_rows)}):", file=sys.stderr)
    for r in cf_rows:
        print(f"  {r['fieldname']} | {r['fieldtype']} | label={r['label']} | after={r['insert_after']}", file=sys.stderr)

    patches = frappe.db.sql(
        """SELECT patch FROM `tabPatch Log`
           WHERE patch LIKE '%erpnext_enhancements%'
           ORDER BY patch""",
        as_dict=True,
    )
    print(f"\nerpnext_enhancements patches in log ({len(patches)}):", file=sys.stderr)
    for p in patches:
        print(f"  {p['patch']}", file=sys.stderr)


def call_forecast() -> None:
    from lcs_integrations.projects.api import get_forecast

    result = get_forecast(period="month", months_ahead=18)
    print(f"buckets: {len(result)}", file=sys.stderr)
    for b in result:
        print(
            f"  period={b['period']} total={b['total_value']} "
            f"weighted={b['weighted_value']:.0f} projects={len(b['projects'])}",
            file=sys.stderr,
        )
        for p in b["projects"]:
            print(
                f"    -> {p['project_name']} ({p['phase']}) "
                f"value={p['value']} prob={p['probability']} weighted={p['weighted']:.0f}",
                file=sys.stderr,
            )


def dump_demo_projects() -> None:
    demo = frappe.get_all(
        "LCS Project",
        filters={"notes": ["like", "%lcs-seed%"]},
        fields=[
            "name",
            "project_name",
            "phase",
            "status",
            "probability",
            "estimated_value",
            "richtpreis",
            "angebot_total",
            "budget_customer",
            "expected_close_date",
            "salesperson",
        ],
        order_by="creation asc",
    )
    for p in demo:
        print(
            f"{p.project_name} | phase={p.phase} status={p.status} "
            f"prob={p.probability} est={p.estimated_value} richt={p.richtpreis} "
            f"ang={p.angebot_total} budget={p.budget_customer} "
            f"close={p.expected_close_date} salesperson={p.salesperson}",
            file=sys.stderr,
        )
