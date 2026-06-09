"""
Remove abas-era custom fields and re-run install_custom_fields to install
the new ERPNext + Fusion Manage field set.

Idempotent — safe to re-run.
"""

import frappe


ABAS_FIELDS_TO_DROP = [
    ("Customer", "abas_id"),
    ("Sales Order", "abas_order_no"),
    ("Sales Order", "lcs_delivery_status"),
    ("Sales Order", "lcs_planned_ship_date"),
    ("Sales Order", "lcs_real_revenue"),
    ("Quotation", "abas_quotation_no"),
    ("Contact", "abas_contact_id"),
    ("Lead", "lcs_source"),  # replaced by CRM Lead Source link on LCS Project
]


def execute():
    for dt, fieldname in ABAS_FIELDS_TO_DROP:
        cf_name = frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": fieldname})
        if not cf_name:
            continue
        try:
            frappe.delete_doc("Custom Field", cf_name, ignore_permissions=True, force=1)
        except Exception as e:
            frappe.log_error(f"Could not drop {dt}.{fieldname}: {e}", "remove_abas_legacy")

    # Re-run install_custom_fields to add the new ERPNext/Fusion fields
    from lcs_integrations.patches.v1_0.install_custom_fields import execute as install
    install()

    frappe.db.commit()
