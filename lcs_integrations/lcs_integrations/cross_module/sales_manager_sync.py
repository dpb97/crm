"""
LCS Project as the single source of truth for sales_manager assignment.

When the sales_manager field changes on an LCS Project, push the new
value onto:
  - the linked CRM Deal (LCS Project.deal)
  - the Lead behind that deal (CRM Deal.lead)

Direction is deliberately one-way — edits on the Deal or Lead side
don't overwrite the project. This keeps the pipeline consistent with
whoever takes ownership at the project stage.
"""

import frappe


def on_project_validate(doc, method=None):
    """Fires via the LCS Project.validate doc_event.

    We only act when sales_manager actually changes — the hook runs on
    every save and we don't want unnecessary writes to Deal/Lead.
    """
    if not doc.has_value_changed("sales_manager"):
        return

    propagate(doc.name, doc.sales_manager)


def propagate(project_name: str, sales_manager: str | None) -> dict:
    """Push sales_manager from LCS Project onto the linked Deal + Lead.
    Returns a summary of what was touched."""
    summary = {"deal": None, "lead": None, "skipped": []}

    # Get the linked deal from the project
    deal = frappe.db.get_value("LCS Project", project_name, "deal")
    if not deal:
        summary["skipped"].append("no linked deal")
        return summary

    # CRM Deal — only write if our custom field exists
    if _has_custom_field("CRM Deal", "sales_manager"):
        try:
            frappe.db.set_value("CRM Deal", deal, "sales_manager", sales_manager, update_modified=False)
            summary["deal"] = deal
        except Exception as e:
            frappe.log_error(
                f"Could not propagate sales_manager to CRM Deal {deal}: {e}",
                "sales_manager_sync",
            )

    # CRM Lead behind the deal — frappe/crm has a `lead` field on Deal
    lead = frappe.db.get_value("CRM Deal", deal, "lead") if frappe.db.exists("CRM Deal", deal) else None
    if lead and _has_custom_field("CRM Lead", "sales_manager"):
        try:
            frappe.db.set_value("CRM Lead", lead, "sales_manager", sales_manager, update_modified=False)
            summary["lead"] = lead
        except Exception as e:
            frappe.log_error(
                f"Could not propagate sales_manager to CRM Lead {lead}: {e}",
                "sales_manager_sync",
            )

    return summary


def _has_custom_field(doctype: str, fieldname: str) -> bool:
    return bool(frappe.db.get_value(
        "Custom Field",
        {"dt": doctype, "fieldname": fieldname},
        "name",
    ))


@frappe.whitelist()
def backfill_all() -> dict:
    """One-shot: for every LCS Project that has a sales_manager set,
    make sure the linked Deal + Lead carry the same value.

    Run after the custom-field install patch, or after bulk-editing
    projects in the admin UI.
    """
    frappe.only_for(["System Manager", "Sales Manager"])
    projects = frappe.get_all(
        "LCS Project",
        filters={"sales_manager": ["is", "set"]},
        fields=["name", "sales_manager"],
    )
    touched = {"deals": 0, "leads": 0, "projects": len(projects)}
    for p in projects:
        r = propagate(p.name, p.sales_manager)
        if r.get("deal"):
            touched["deals"] += 1
        if r.get("lead"):
            touched["leads"] += 1
    frappe.db.commit()
    return touched
