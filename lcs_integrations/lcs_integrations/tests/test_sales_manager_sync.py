"""End-to-end test: sales_manager on LCS Project propagates to Deal + Lead."""

import frappe


def run():
    # Use an existing project that has a deal linked
    candidates = frappe.get_all(
        "LCS Project",
        filters={"deal": ["is", "set"]},
        fields=["name", "deal"],
        limit=1,
    )
    if not candidates:
        print("[FAIL] No project with a linked deal to test against")
        return
    project_name = candidates[0]["name"]
    deal_name = candidates[0]["deal"]
    print(f"Using project {project_name} → deal {deal_name}")

    # Pick a real user (Administrator is always present)
    test_user = "Administrator"

    # Set sales_manager — triggers the hook
    project = frappe.get_doc("LCS Project", project_name)
    project.sales_manager = test_user
    project.save(ignore_permissions=True)
    frappe.db.commit()

    # Verify deal got it
    deal_sm = frappe.db.get_value("CRM Deal", deal_name, "sales_manager")
    if deal_sm == test_user:
        print(f"[PASS] Deal {deal_name} now has sales_manager = {deal_sm}")
    else:
        print(f"[FAIL] Deal sales_manager is {deal_sm!r}, expected {test_user!r}")

    # And the lead behind that deal
    lead_name = frappe.db.get_value("CRM Deal", deal_name, "lead")
    if lead_name:
        lead_sm = frappe.db.get_value("CRM Lead", lead_name, "sales_manager")
        if lead_sm == test_user:
            print(f"[PASS] Lead {lead_name} now has sales_manager = {lead_sm}")
        else:
            print(f"[FAIL] Lead sales_manager is {lead_sm!r}, expected {test_user!r}")
    else:
        print(f"[INFO] Deal {deal_name} has no linked lead; skipping lead check")

    # Idempotency — re-save should not error
    project.save(ignore_permissions=True)
    print("[PASS] Re-save did not raise")

    # Cleanup — reset the field to not pollute demo data
    project.sales_manager = None
    project.save(ignore_permissions=True)
    frappe.db.commit()
    print("cleanup: reset sales_manager to None")
