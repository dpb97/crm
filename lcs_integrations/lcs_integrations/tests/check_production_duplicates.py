"""
Scan the production DB for duplicate / dangling cross-module references.

Read-only — safe to run against a live site.
"""

import frappe


def run():
    print("=== Cross-module consistency audit ===\n")

    # 1. Duplicate Customers
    dups = frappe.db.sql(
        "SELECT customer_name, COUNT(*) c FROM `tabCustomer` GROUP BY customer_name HAVING c > 1",
        as_dict=True,
    )
    _print(f"Customers with duplicate customer_name: {len(dups)}", dups)

    # 2. CRM Organizations pointing to non-existent Customer
    bad_cust = frappe.db.sql(
        """SELECT o.name, o.erpnext_customer FROM `tabCRM Organization` o
           WHERE o.erpnext_customer IS NOT NULL AND o.erpnext_customer != ''
             AND NOT EXISTS (SELECT 1 FROM `tabCustomer` c WHERE c.name = o.erpnext_customer)""",
        as_dict=True,
    )
    _print(f"CRM Orgs with dangling ERPNext Customer link: {len(bad_cust)}", bad_cust[:5])

    # 3. LCS Offers with dangling Quotation link
    bad_qtn = frappe.db.sql(
        """SELECT o.name, o.erpnext_quotation FROM `tabLCS Offer` o
           WHERE o.erpnext_quotation IS NOT NULL
             AND NOT EXISTS (SELECT 1 FROM `tabQuotation` q WHERE q.name = o.erpnext_quotation)""",
        as_dict=True,
    )
    _print(f"LCS Offers with dangling Quotation link: {len(bad_qtn)}", bad_qtn[:5])

    # 4. LCS Offers with dangling Sales Order link
    bad_so = frappe.db.sql(
        """SELECT o.name, o.erpnext_sales_order FROM `tabLCS Offer` o
           WHERE o.erpnext_sales_order IS NOT NULL
             AND NOT EXISTS (SELECT 1 FROM `tabSales Order` s WHERE s.name = o.erpnext_sales_order)""",
        as_dict=True,
    )
    _print(f"LCS Offers with dangling Sales Order link: {len(bad_so)}", bad_so[:5])

    # 5. LCS Projects with dangling BSM Project link
    if frappe.db.exists("DocType", "BSM Project"):
        bad_bsm = frappe.db.sql(
            """SELECT p.name, p.bsm_project FROM `tabLCS Project` p
               WHERE p.bsm_project IS NOT NULL AND p.bsm_project != ''
                 AND NOT EXISTS (SELECT 1 FROM `tabBSM Project` b WHERE b.name = p.bsm_project)""",
            as_dict=True,
        )
        _print(f"LCS Projects with dangling BSM Project link: {len(bad_bsm)}", bad_bsm[:5])

    # 6. Back-link integrity: Quotation.lcs_offer → LCS Offer exists
    if _has_cf("Quotation", "lcs_offer"):
        bad_back = frappe.db.sql(
            """SELECT q.name, q.lcs_offer FROM `tabQuotation` q
               WHERE q.lcs_offer IS NOT NULL AND q.lcs_offer != ''
                 AND NOT EXISTS (SELECT 1 FROM `tabLCS Offer` o WHERE o.name = q.lcs_offer)""",
            as_dict=True,
        )
        _print(f"Quotations pointing at deleted LCS Offer: {len(bad_back)}", bad_back[:5])

    # 7. source field — all values must exist in CRM Lead Source
    # (we used raw string compare to avoid IN subquery issues)
    invalid_sources = frappe.db.sql(
        """SELECT DISTINCT source FROM `tabLCS Project`
           WHERE source IS NOT NULL AND source != ''""",
        as_dict=True,
    )
    valid_sources = set(frappe.get_all("CRM Lead Source", pluck="name"))
    missing = [r.source for r in invalid_sources if r.source not in valid_sources]
    _print(f"LCS Project.source values not in CRM Lead Source: {missing}", missing)

    # 8. Offer version uniqueness per project
    dup_versions = frappe.db.sql(
        """SELECT project, version, COUNT(*) c FROM `tabLCS Offer`
           WHERE project IS NOT NULL AND version IS NOT NULL
           GROUP BY project, version HAVING c > 1""",
        as_dict=True,
    )
    _print(f"Duplicate offer versions (same project+version): {len(dup_versions)}", dup_versions[:5])

    # 9. Master data counts
    print()
    print(f"CRM Lead Sources: {frappe.db.count('CRM Lead Source')}")
    print(f"CRM Lost Reasons: {frappe.db.count('CRM Lost Reason')}")
    print(f"LCS Projects total: {frappe.db.count('LCS Project')}")
    print(f"LCS Offers total: {frappe.db.count('LCS Offer')}")
    print(f"LCS Offer Templates: {frappe.db.count('LCS Offer Template')}")
    if frappe.db.exists("DocType", "BSM Project"):
        print(f"BSM Projects total: {frappe.db.count('BSM Project')}")

    print("\n=== Audit complete ===")


def _print(label, detail):
    emoji = "OK  " if not detail or (isinstance(detail, list) and not detail) else "WARN"
    print(f"[{emoji}] {label}")
    if detail and isinstance(detail, list):
        for row in detail:
            print(f"       {row}")


def _has_cf(dt, fn):
    return bool(frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": fn}))
