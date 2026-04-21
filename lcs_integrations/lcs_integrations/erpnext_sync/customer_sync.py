"""
CRM Organization ↔ ERPNext Customer sync.

ERPNext is installed alongside frappe/crm on the LCS bench. CRM keeps
the lead-stage organization record; once a deal is won we need a
Customer in ERPNext so Sales Orders and invoicing have somewhere to live.

Sync is one-directional (CRM → ERPNext) to avoid loops.
"""

import frappe
from frappe import _


def on_organization_created(doc, method=None):
    """After a new CRM Organization is saved, mirror it as an ERPNext Customer."""
    sync_to_erpnext(doc)


def on_organization_updated(doc, method=None):
    """Keep the ERPNext Customer's core fields in sync with the CRM record."""
    if not doc.has_value_changed("organization_name") and not doc.has_value_changed("website"):
        return
    sync_to_erpnext(doc)


def sync_to_erpnext(org):
    """Upsert an ERPNext Customer matching the given CRM Organization."""
    if not frappe.db.exists("DocType", "Customer"):
        # ERPNext not installed on this site — silently skip.
        return

    customer_name = org.organization_name
    if not customer_name:
        return

    if frappe.db.exists("Customer", customer_name):
        customer = frappe.get_doc("Customer", customer_name)
    else:
        customer = frappe.new_doc("Customer")
        customer.customer_name = customer_name
        customer.customer_type = "Company"

    # Fields worth mirroring — keep it minimal and additive to avoid
    # clobbering ERPNext-side edits users may make.
    if getattr(org, "website", None):
        customer.website = org.website
    if getattr(org, "industry", None):
        customer.industry = org.industry
    if getattr(org, "territory", None):
        customer.territory = org.territory

    try:
        customer.save(ignore_permissions=True)
    except frappe.DuplicateEntryError:
        pass
    frappe.db.commit()
    return customer.name
