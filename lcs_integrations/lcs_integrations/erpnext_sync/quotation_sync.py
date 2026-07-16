"""
LCS Offer → ERPNext Quotation sync.

Behaviour:
- Status 'Sent'     → create/update matching Quotation (submit=False)
- Status 'Accepted' → create Sales Order from the Quotation
- Status 'Rejected' → mark Quotation as Lost (ERPNext's own status field)

The CRM-side LCS Offer stays the source of truth for negotiation data
(version history, contact, notes). ERPNext gets the commercial
artefacts (dates, values, items for fulfilment).
"""

import frappe
from frappe import _


def on_offer_updated(doc, method=None):
    """Route based on status transitions."""
    if not doc.has_value_changed("status"):
        return

    if doc.status == "Sent":
        upsert_quotation(doc)
    elif doc.status == "Accepted":
        upsert_quotation(doc)  # ensure Quotation exists and is up-to-date
        create_sales_order(doc)
    elif doc.status == "Rejected":
        mark_quotation_lost(doc)


def upsert_quotation(offer):
    """Create or update the ERPNext Quotation linked to this LCS Offer."""
    if not frappe.db.exists("DocType", "Quotation"):
        return

    project = frappe.get_doc("LCS Project", offer.project)
    customer = _ensure_customer(project)
    if not customer:
        frappe.log_error(
            f"Cannot create Quotation for {offer.name}: no customer on project {project.name}",
            "erpnext_sync.quotation",
        )
        return

    existing_name = offer.get("erpnext_quotation")
    if existing_name and frappe.db.exists("Quotation", existing_name):
        quotation = frappe.get_doc("Quotation", existing_name)
    else:
        quotation = frappe.new_doc("Quotation")
        quotation.quotation_to = "Customer"
        quotation.party_name = customer

    quotation.transaction_date = offer.offer_date or frappe.utils.nowdate()
    quotation.valid_till = offer.valid_until
    quotation.currency = offer.currency or "EUR"
    # Back-link so duplicate detection + integration_status can find us
    if hasattr(quotation, "lcs_offer"):
        quotation.lcs_offer = offer.name

    # Add a single item placeholder for the total value if items list is empty
    # (real items come from Fusion Manage BOM sync — stub for now)
    if not quotation.get("items"):
        quotation.append("items", {
            "item_code": _placeholder_item_code(),
            "qty": 1,
            "rate": offer.value or 0,
            "description": offer.offer_title or project.project_name,
        })
    elif offer.value:
        # Update placeholder rate if value changed
        quotation.items[0].rate = offer.value

    try:
        quotation.save(ignore_permissions=True)
        frappe.db.set_value("LCS Offer", offer.name, "erpnext_quotation", quotation.name)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Quotation sync failed for {offer.name}: {e}", "erpnext_sync.quotation")


def create_sales_order(offer):
    """Create an ERPNext Sales Order from the accepted offer's Quotation."""
    if not frappe.db.exists("DocType", "Sales Order"):
        return

    quotation_name = offer.get("erpnext_quotation")
    if not quotation_name or not frappe.db.exists("Quotation", quotation_name):
        return

    if offer.get("erpnext_sales_order") and frappe.db.exists("Sales Order", offer.erpnext_sales_order):
        return  # already created

    quotation = frappe.get_doc("Quotation", quotation_name)
    if quotation.docstatus != 1:
        # ERPNext requires submitted Quotation to convert — submit first
        try:
            quotation.submit()
        except Exception as e:
            frappe.log_error(f"Could not submit quotation {quotation_name}: {e}", "erpnext_sync.sales_order")
            return

    try:
        from erpnext.selling.doctype.quotation.quotation import make_sales_order
        so = make_sales_order(quotation.name)
        so.delivery_date = frappe.utils.add_days(frappe.utils.nowdate(), 90)
        # Back-link to project so after_insert hook can spawn BSM Project
        if hasattr(so, "lcs_project"):
            so.lcs_project = offer.project
        so.insert(ignore_permissions=True)
        frappe.db.set_value("LCS Offer", offer.name, "erpnext_sales_order", so.name)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Sales Order creation failed for {offer.name}: {e}", "erpnext_sync.sales_order")


def mark_quotation_lost(offer):
    """Flag the linked Quotation as lost when the offer is rejected."""
    quotation_name = offer.get("erpnext_quotation")
    if not quotation_name or not frappe.db.exists("Quotation", quotation_name):
        return
    try:
        frappe.db.set_value("Quotation", quotation_name, "status", "Lost")
        if offer.lost_reason:
            frappe.db.set_value("Quotation", quotation_name, "order_lost_reason", offer.lost_reason)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Mark-lost failed for {quotation_name}: {e}", "erpnext_sync.quotation")


def _ensure_customer(project):
    """Return the ERPNext Customer for the project, creating one if needed."""
    if project.get("erpnext_customer") and frappe.db.exists("Customer", project.erpnext_customer):
        return project.erpnext_customer
    if not project.organization:
        return None
    org = frappe.get_doc("CRM Organization", project.organization)
    from lcs_integrations.erpnext_sync.customer_sync import sync_to_erpnext
    customer_name = sync_to_erpnext(org)
    if customer_name:
        frappe.db.set_value("LCS Project", project.name, "erpnext_customer", customer_name)
    return customer_name


def _placeholder_item_code():
    """Return a generic service-item code so Quotations can be drafted
    before real BOM sync from Fusion Manage kicks in."""
    code = "LCS-QUOTE-PLACEHOLDER"
    if not frappe.db.exists("Item", code):
        try:
            item = frappe.new_doc("Item")
            item.item_code = code
            item.item_name = "LCS Quote Placeholder"
            item.item_group = frappe.db.get_value("Item Group", {"is_group": 0}, "name") or "All Item Groups"
            item.stock_uom = "Nos"
            item.is_stock_item = 0
            item.insert(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            pass
    return code
