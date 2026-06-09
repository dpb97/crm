import frappe


def run():
    # Clean __TEST__ data first
    for n in frappe.get_all("LCS Project", {"project_name": ["like", "__TEST_DTP__%"]}, pluck="name"):
        frappe.delete_doc("LCS Project", n, ignore_permissions=True, force=1)
    for n in frappe.get_all("CRM Deal", {"organization": ["like", "__TEST_DTP__%"]}, pluck="name"):
        frappe.delete_doc("CRM Deal", n, ignore_permissions=True, force=1)
    for n in frappe.get_all("CRM Lead", {"organization": ["like", "__TEST_DTP__%"]}, pluck="name"):
        frappe.delete_doc("CRM Lead", n, ignore_permissions=True, force=1)
    for n in frappe.get_all("CRM Organization", {"organization_name": ["like", "__TEST_DTP__%"]}, pluck="name"):
        frappe.delete_doc("CRM Organization", n, ignore_permissions=True, force=1)
    frappe.db.commit()

    print("=== Pipeline totals ===")
    print(f"  CRM Leads:        {frappe.db.count('CRM Lead')}")
    print(f"  CRM Deals:        {frappe.db.count('CRM Deal')}")
    print(f"  LCS Projects:     {frappe.db.count('LCS Project')}")
    print(f"  LCS Offers:       {frappe.db.count('LCS Offer')}")
    print(f"  BSM Projects:     {frappe.db.count('BSM Project')}")

    print("\n=== Coverage ===")
    deals_with_lead = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabCRM Deal` WHERE lead IS NOT NULL AND lead != ''"
    )[0][0]
    projects_with_deal = frappe.db.count('LCS Project', {"deal": ["is", "set"]})
    projects_with_bsm = frappe.db.count('LCS Project', {"bsm_project": ["is", "set"]})
    print(f"  Deals with Lead:          {deals_with_lead}/{frappe.db.count('CRM Deal')}")
    print(f"  Projects with Deal:       {projects_with_deal}/{frappe.db.count('LCS Project')}")
    print(f"  Projects with BSM Site:   {projects_with_bsm}/{frappe.db.count('LCS Project')}")
