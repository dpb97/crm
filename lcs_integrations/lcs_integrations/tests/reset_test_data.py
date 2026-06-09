"""Reset anything created by test_integration_e2e so the tests run clean."""

import frappe


def run():
    # Delete all __TEST__ offers, quotations, sales orders, BSM projects, LCS projects
    test_offers = frappe.get_all("LCS Offer", {"offer_title": ["like", "__TEST__%"]}, pluck="name")
    for o in test_offers:
        try:
            frappe.delete_doc("LCS Offer", o, ignore_permissions=True, force=1)
        except Exception:
            pass

    test_projects = frappe.get_all("LCS Project", {"project_name": ["like", "__TEST__%"]}, pluck="name")
    for p in test_projects:
        # Delete linked BSM Project first
        if frappe.db.exists("DocType", "BSM Project"):
            bsms = frappe.get_all("BSM Project", {"lcs_project": p}, pluck="name") if _cf("BSM Project", "lcs_project") else []
            for b in bsms:
                try:
                    frappe.delete_doc("BSM Project", b, ignore_permissions=True, force=1)
                except Exception:
                    pass
        # Sales Orders linked
        if _cf("Sales Order", "lcs_project"):
            sos = frappe.get_all("Sales Order", {"lcs_project": p}, pluck="name")
            for s in sos:
                try:
                    frappe.delete_doc("Sales Order", s, ignore_permissions=True, force=1)
                except Exception:
                    pass
        try:
            frappe.delete_doc("LCS Project", p, ignore_permissions=True, force=1)
        except Exception:
            pass

    # Delete orphan quotations that had our test offers (now gone)
    if _cf("Quotation", "lcs_offer"):
        qtns = frappe.db.sql(
            """SELECT name FROM `tabQuotation` q
               WHERE q.lcs_offer IS NOT NULL
                 AND NOT EXISTS (SELECT 1 FROM `tabLCS Offer` o WHERE o.name = q.lcs_offer)""",
            as_dict=True,
        )
        for row in qtns:
            try:
                frappe.delete_doc("Quotation", row.name, ignore_permissions=True, force=1)
            except Exception:
                pass

    # Customers + orgs with __TEST__ prefix
    for c in frappe.get_all("Customer", {"customer_name": ["like", "__TEST__%"]}, pluck="name"):
        try:
            frappe.delete_doc("Customer", c, ignore_permissions=True, force=1)
        except Exception:
            pass
    for o in frappe.get_all("CRM Organization", {"organization_name": ["like", "__TEST__%"]}, pluck="name"):
        try:
            frappe.delete_doc("CRM Organization", o, ignore_permissions=True, force=1)
        except Exception:
            pass

    frappe.db.commit()
    print("Test data reset complete.")


def _cf(dt, fn):
    return bool(frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": fn}))
