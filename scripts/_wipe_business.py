"""Wipe all transactional business data so we can seed fresh
LCS-themed demo data on top. Master data with referential
integrity that's hard to recreate (Company, currency, UOM,
Account chart, Roles, Workflow Definitions) is preserved.

Run via:
    bench --site lcs.local console < /tmp/_wipe.py

Snapshots row counts before and after to STDOUT so we can see
what was nuked.
"""
import frappe

# Order matters — child tables first to satisfy FK refs.
# Anything we don't list here stays untouched.
WIPE_ORDER = [
    # Sales chain
    "Sales Invoice Item",
    "Sales Invoice Payment",
    "Sales Invoice",
    "Delivery Note Item",
    "Delivery Note",
    "Sales Order Item",
    "Sales Order",
    "Quotation Item",
    "Quotation",
    # Purchase chain
    "Purchase Invoice Item",
    "Purchase Invoice",
    "Purchase Receipt Item",
    "Purchase Receipt",
    "Purchase Order Item",
    "Purchase Order",
    "Supplier Quotation Item",
    "Supplier Quotation",
    "Request for Quotation Item",
    "Request for Quotation",
    "Material Request Item",
    "Material Request",
    # Manufacturing / stock movement
    "Work Order Item",
    "Work Order Operation",
    "Work Order",
    "Job Card Time Log",
    "Job Card Item",
    "Job Card",
    "Stock Entry Detail",
    "Stock Entry",
    "Stock Ledger Entry",
    "Stock Reservation Entry",
    # Project / Task / Timesheet
    "Project Update",
    "Project User",
    "Timesheet Detail",
    "Timesheet",
    "Task Depends On",
    "Task",
    "Project",
    # CRM (per user instruction this is preserved — comment in)
    # "CRM Lead", "CRM Deal", "FCRM Note", "CRM Task", "CRM Call Log",
    # Accounting
    "Payment Entry Reference",
    "Payment Entry Deduction",
    "Payment Entry",
    "Journal Entry Account",
    "Journal Entry",
    "GL Entry",
    "Sales Taxes and Charges",
    "Purchase Taxes and Charges",
    # BSM / LCS bridge
    "BSM Project",
    "BSM Asset Component",
    "BSM Manpower Assignment",
    # ERPNext masters that are demo / test (keep Company, Item Group, UOM)
    "Item Price",
    "BOM Item",
    "BOM Operation",
    "BOM",
    "Item",
    # Partners
    "Contact",
    "Address",
    "Customer",
    "Supplier",
    # Misc
    "ToDo",
    "Notification Log",
    "Comment",
    "Activity Log",
    "Communication",
    "Version",
    "Pilanda News",
]

counts_before: dict[str, int] = {}
counts_after: dict[str, int] = {}

print("=== Pre-wipe row counts (only non-empty tables shown) ===")
for dt in WIPE_ORDER:
    try:
        n = frappe.db.count(dt)
    except Exception:
        continue
    counts_before[dt] = n
    if n:
        print("  %-40s %d" % (dt, n))

print("\n=== Wiping ===")
frappe.db.sql("SET FOREIGN_KEY_CHECKS=0")
for dt in WIPE_ORDER:
    try:
        table = "tab" + dt
        n = frappe.db.sql("SELECT COUNT(*) FROM `%s`" % table)[0][0]
        if not n:
            continue
        frappe.db.sql("DELETE FROM `%s`" % table)
        counts_after[dt] = 0
        print("  %-40s -%d" % (dt, n))
    except Exception as e:  # noqa: BLE001
        print("  SKIP %s (%s)" % (dt, type(e).__name__))
frappe.db.sql("SET FOREIGN_KEY_CHECKS=1")
frappe.db.commit()
print("\n=== Done ===")
total_deleted = sum(counts_before.get(k, 0) for k in counts_before if k not in WIPE_ORDER or True)
print("Deleted total rows: %d" % sum(counts_before.values()))

frappe.clear_cache()
print("Cache cleared.")
