import frappe
from collections import defaultdict

crm_modules = [r["name"] for r in frappe.get_all("Module Def", filters={"app_name":"crm"}, fields=["name"], limit=0)]
crm = {r["name"] for r in frappe.get_all("DocType", filters={"module":["in",crm_modules]}, fields=["name"], limit=0)}
print("CRM doctypes kept: %d" % len(crm))

cfs = frappe.get_all("Custom Field", fields=["name","dt","fieldname","label","fieldtype","is_system_generated","owner"], limit=0)
user_cfs = [c for c in cfs if c["dt"] not in crm and not int(c.get("is_system_generated") or 0)]
print("\nCustom Fields outside CRM, user-added: %d" % len(user_cfs))
by_dt = defaultdict(list)
for c in user_cfs:
    by_dt[c["dt"]].append(c)
for dt, rows in sorted(by_dt.items()):
    fields = ", ".join(r["fieldname"] for r in rows[:6])
    extra = " ..." if len(rows) > 6 else ""
    print("  %-45s (%d) -> %s%s" % (dt, len(rows), fields, extra))

ps = frappe.get_all("Property Setter", fields=["name","doc_type","field_name","property","is_system_generated"], limit=0)
user_ps = [p for p in ps if p["doc_type"] not in crm and not int(p.get("is_system_generated") or 0)]
print("\nProperty Setters outside CRM, user-added: %d" % len(user_ps))
by_dt2 = defaultdict(list)
for p in user_ps:
    by_dt2[p["doc_type"]].append(p)
for dt, rows in sorted(by_dt2.items()):
    print("  %-45s (%d)" % (dt, len(rows)))

cs = frappe.get_all("Client Script", fields=["name","dt","view","enabled","owner"], limit=0)
user_cs = [c for c in cs if c["dt"] not in crm]
print("\nClient Scripts outside CRM: %d" % len(user_cs))
for c in user_cs:
    print("  %-40s view=%s enabled=%s name=%s" % (c["dt"], c["view"], c["enabled"], c["name"]))

ss = frappe.get_all("Server Script", fields=["name","script_type","reference_doctype","doctype_event","disabled"], limit=0)
user_ss = [s for s in ss if (s.get("reference_doctype") or "") not in crm]
print("\nServer Scripts outside CRM: %d" % len(user_ss))
for s in user_ss:
    ref = s.get("reference_doctype") or "(none)"
    print("  ref=%-30s type=%-12s event=%s name=%s" % (ref, s["script_type"], s.get("doctype_event","-"), s["name"]))
