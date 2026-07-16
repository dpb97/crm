import frappe
for dt in ["Customer", "Supplier", "Item", "Project", "Task", "Pilanda News"]:
    print("  %-15s %d" % (dt, frappe.db.count(dt)))
print("  Custom Field (outside CRM, user-added)")
crm_mods = [r["name"] for r in frappe.get_all("Module Def", filters={"app_name":"crm"}, fields=["name"], limit=0)]
crm = {r["name"] for r in frappe.get_all("DocType", filters={"module":["in",crm_mods]}, fields=["name"], limit=0)}
cfs = frappe.get_all("Custom Field", fields=["dt","is_system_generated"], limit=0)
user_cfs = [c for c in cfs if c["dt"] not in crm and not int(c.get("is_system_generated") or 0)]
print("                  %d" % len(user_cfs))
