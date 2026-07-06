"""Drop the 244 Custom Fields + 60 Property Setters that were
restored earlier — user wants vanilla doctypes again.
"""
import frappe

crm_modules = [r["name"] for r in frappe.get_all("Module Def", filters={"app_name":"crm"}, fields=["name"], limit=0)]
crm = {r["name"] for r in frappe.get_all("DocType", filters={"module":["in",crm_modules]}, fields=["name"], limit=0)}

cfs = frappe.get_all("Custom Field", fields=["name","dt","is_system_generated"], limit=0)
victims_cf = [c["name"] for c in cfs if c["dt"] not in crm and not int(c.get("is_system_generated") or 0)]
ps = frappe.get_all("Property Setter", fields=["name","doc_type","is_system_generated"], limit=0)
victims_ps = [p["name"] for p in ps if p["doc_type"] not in crm and not int(p.get("is_system_generated") or 0)]

if victims_cf:
    ph = ",".join(["%s"] * len(victims_cf))
    frappe.db.sql("DELETE FROM `tabCustom Field` WHERE name IN (%s)" % ph, victims_cf)
if victims_ps:
    ph = ",".join(["%s"] * len(victims_ps))
    frappe.db.sql("DELETE FROM `tabProperty Setter` WHERE name IN (%s)" % ph, victims_ps)

frappe.db.commit()
frappe.clear_cache()
print("Re-deleted %d CFs, %d PSes" % (len(victims_cf), len(victims_ps)))
