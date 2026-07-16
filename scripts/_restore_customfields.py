"""Restore Custom Fields + Property Setters from the purge
snapshot so the installed apps' validate hooks (next_pms,
fusion_manage, bsm, ...) stop crashing on missing custom_*
attributes.

The data wipe (separate step) stays — only metadata comes back.
"""
import frappe
import json
import os
import glob

snapshots = sorted(glob.glob("/home/dboeckle/frappe-bench/sites/lcs.local/private/pilanda_purges/snapshot_*.json"))
if not snapshots:
    print("No snapshot found.")
else:
    snap = snapshots[-1]
    print("Restoring from: %s" % snap)
    with open(snap) as f:
        data = json.load(f)

    cf_rows = data.get("custom_fields", [])
    ps_rows = data.get("property_setters", [])

    cf_inserted = 0
    cf_skipped = 0
    for row in cf_rows:
        if frappe.db.exists("Custom Field", row["name"]):
            cf_skipped += 1; continue
        try:
            d = frappe.new_doc("Custom Field")
            for k, v in row.items():
                if k in ("doctype", "creation", "modified"):
                    continue
                try:
                    d.set(k, v)
                except Exception:
                    pass
            d.insert(ignore_permissions=True, ignore_mandatory=True)
            cf_inserted += 1
        except Exception as e:  # noqa: BLE001
            print("  CF FAIL %s.%s : %s" % (row.get("dt"), row.get("fieldname"), e))
    print("Custom Fields restored: %d (skipped existing: %d)" % (cf_inserted, cf_skipped))

    ps_inserted = 0
    ps_skipped = 0
    for row in ps_rows:
        if frappe.db.exists("Property Setter", row["name"]):
            ps_skipped += 1; continue
        try:
            d = frappe.new_doc("Property Setter")
            for k, v in row.items():
                if k in ("doctype", "creation", "modified"):
                    continue
                try:
                    d.set(k, v)
                except Exception:
                    pass
            d.insert(ignore_permissions=True, ignore_mandatory=True)
            ps_inserted += 1
        except Exception as e:  # noqa: BLE001
            print("  PS FAIL %s : %s" % (row.get("name"), e))
    print("Property Setters restored: %d (skipped existing: %d)" % (ps_inserted, ps_skipped))

    frappe.db.commit()
    frappe.clear_cache()
    print("Done.")
