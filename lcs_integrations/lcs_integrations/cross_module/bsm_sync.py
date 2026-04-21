"""
ERPNext Sales Order → BSM Project auto-creation.

When an accepted LCS Offer produces an ERPNext Sales Order, we also
spin up a BSM construction-site project so field staff can start
logging daily reports, defects, equipment usage, and hours against it.
Everything chains back to the originating LCS Project.
"""

import frappe


def on_sales_order_created(doc, method=None):
    """Create a BSM Project mirror for a new Sales Order that has
    lcs_project set."""
    if not frappe.db.exists("DocType", "BSM Project"):
        return
    lcs_project_name = doc.get("lcs_project")
    if not lcs_project_name:
        return

    lcs = frappe.get_doc("LCS Project", lcs_project_name)
    if lcs.bsm_project and frappe.db.exists("BSM Project", lcs.bsm_project):
        # Already linked — nothing to do
        return

    try:
        bsm = frappe.new_doc("BSM Project")
        bsm.project_name = lcs.project_name
        if hasattr(bsm, "sales_order"):
            bsm.sales_order = doc.name
        if hasattr(bsm, "lcs_project"):
            bsm.lcs_project = lcs.name
        if hasattr(bsm, "customer"):
            bsm.customer = lcs.erpnext_customer or lcs.organization
        if hasattr(bsm, "country"):
            bsm.country = lcs.country
        if hasattr(bsm, "planned_start_date"):
            bsm.planned_start_date = doc.delivery_date or frappe.utils.nowdate()
        bsm.insert(ignore_permissions=True)
        frappe.db.set_value("LCS Project", lcs.name, "bsm_project", bsm.name)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"BSM project creation failed for SO {doc.name}: {e}", "bsm_sync")
