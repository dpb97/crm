"""End-to-end test: Deal marked Won → LCS Project auto-created."""

import frappe


def run():
    # Create a fresh organization + deal that definitely has no project yet
    org_name = "__TEST_DTP__ DemoCustomer"
    if not frappe.db.exists("CRM Organization", org_name):
        org = frappe.new_doc("CRM Organization")
        org.organization_name = org_name
        org.insert(ignore_permissions=True)

    deal = frappe.new_doc("CRM Deal")
    deal.organization = org_name
    deal.deal_name = "__TEST_DTP__ Seilbahn Demo"
    deal.annual_revenue = 500000
    deal.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"Created test deal: {deal.name}")

    # Verify no project yet
    existing = frappe.db.get_value("LCS Project", {"deal": deal.name}, "name")
    print(f"Project linked before Won: {existing or '(none)'}")

    # Flip to Won — should fire the hook
    deal.status = "Won"
    deal.save(ignore_permissions=True)
    frappe.db.commit()

    # Verify project now exists
    created = frappe.db.get_value("LCS Project", {"deal": deal.name}, ["name", "project_name", "project_type", "phase"], as_dict=True)
    if created:
        print(f"[PASS] Auto-created: {created.name} · {created.project_name} · type={created.project_type} · phase={created.phase}")
    else:
        print(f"[FAIL] No project was created")

    # Re-save — idempotency check
    deal.save(ignore_permissions=True)
    count = frappe.db.count("LCS Project", {"deal": deal.name})
    if count == 1:
        print(f"[PASS] Idempotent — still {count} project after re-save")
    else:
        print(f"[FAIL] Non-idempotent — now {count} projects")

    return {"deal": deal.name, "project": created}


def cleanup():
    for n in frappe.get_all("LCS Project", {"project_name": ["like", "__TEST_DTP__%"]}, pluck="name"):
        frappe.delete_doc("LCS Project", n, ignore_permissions=True, force=1)
    for n in frappe.get_all("CRM Deal", {"deal_name": ["like", "__TEST_DTP__%"]}, pluck="name"):
        frappe.delete_doc("CRM Deal", n, ignore_permissions=True, force=1)
    for n in frappe.get_all("CRM Organization", {"organization_name": ["like", "__TEST_DTP__%"]}, pluck="name"):
        frappe.delete_doc("CRM Organization", n, ignore_permissions=True, force=1)
    frappe.db.commit()
    print("cleanup done")
