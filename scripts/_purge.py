import frappe
import json
import os
from datetime import datetime

# Build the CRM doctype set — these are the only customisations
# we keep. Everything else gets purged.
crm_modules = [r["name"] for r in frappe.get_all("Module Def", filters={"app_name":"crm"}, fields=["name"], limit=0)]
crm = {r["name"] for r in frappe.get_all("DocType", filters={"module":["in",crm_modules]}, fields=["name"], limit=0)}
print("CRM doctypes kept: %d" % len(crm))

# Snapshot what we're about to nuke — easier than restoring the
# full SQL backup if the user wants a single field back.
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
snapshot_dir = "/home/dboeckle/frappe-bench/sites/lcs.local/private/pilanda_purges"
os.makedirs(snapshot_dir, exist_ok=True)

cfs = frappe.get_all("Custom Field", fields=["*"], limit=0)
victims_cf = [c for c in cfs if c["dt"] not in crm and not int(c.get("is_system_generated") or 0)]
ps = frappe.get_all("Property Setter", fields=["*"], limit=0)
victims_ps = [p for p in ps if p["doc_type"] not in crm and not int(p.get("is_system_generated") or 0)]

snap_path = os.path.join(snapshot_dir, "snapshot_%s.json" % stamp)
with open(snap_path, "w") as f:
    json.dump(
        {"custom_fields": victims_cf, "property_setters": victims_ps},
        f, default=str, indent=2,
    )
print("Snapshot written to: %s" % snap_path)
print("  %d Custom Fields, %d Property Setters" % (len(victims_cf), len(victims_ps)))

# Hard-delete via SQL (frappe.delete_doc would be ~5 min for 286
# rows because each runs its own validations). The delete is
# wrapped in an explicit transaction.
cf_names = [v["name"] for v in victims_cf]
ps_names = [v["name"] for v in victims_ps]

if cf_names:
    placeholders = ",".join(["%s"] * len(cf_names))
    frappe.db.sql("DELETE FROM `tabCustom Field` WHERE name IN (%s)" % placeholders, cf_names)
if ps_names:
    placeholders = ",".join(["%s"] * len(ps_names))
    frappe.db.sql("DELETE FROM `tabProperty Setter` WHERE name IN (%s)" % placeholders, ps_names)

frappe.db.commit()
print("Deleted %d Custom Fields, %d Property Setters" % (len(cf_names), len(ps_names)))

# Clear caches so the doctype meta picks up the new shape.
frappe.clear_cache()
print("Cache cleared.")
