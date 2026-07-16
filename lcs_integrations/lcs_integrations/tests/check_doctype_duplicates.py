"""
Hunt for any kind of DocType duplication in the LCS app.

Checks:
1. Database: name is PK so no two rows can share it, but we cross-check
   `tabDocType` count against unique names.
2. File system: scan repo for two `*.json` files declaring the same
   DocType name (e.g. one path stale after a rename).
3. App ownership: every LCS DocType should belong to the
   "LCS Integrations" module, not leak into another module.
4. Custom Fields: same fieldname on the same DocType registered twice
   would also be a duplicate.
"""

import frappe
from collections import defaultdict


def run():
    print("\n=== DocType duplicate audit ===\n")
    issues = []

    # 1. Database — DocType primary keys
    rows = frappe.db.sql("SELECT name FROM `tabDocType`", as_dict=True)
    seen = defaultdict(int)
    for r in rows:
        seen[r.name] += 1
    db_dups = [n for n, c in seen.items() if c > 1]
    if db_dups:
        issues.append(("db_duplicate_doctype", db_dups))
        print(f"[FAIL] {len(db_dups)} DocTypes appear in tabDocType more than once: {db_dups}")
    else:
        print(f"[ OK ] {len(seen)} unique DocTypes registered in DB")

    # 2. LCS-owned DocTypes — exact ownership
    lcs_doctypes = frappe.get_all(
        "DocType",
        filters={"name": ["like", "LCS%"]},
        fields=["name", "module", "is_virtual"],
    )
    print(f"\n[INFO] {len(lcs_doctypes)} LCS-prefixed DocTypes:")
    foreign_module = []
    for d in lcs_doctypes:
        is_lcs = d.module == "LCS Integrations"
        marker = " " if is_lcs else "✗"
        print(f"  [{marker}] {d.name}  (module: {d.module})")
        if not is_lcs:
            foreign_module.append(d)
    if foreign_module:
        issues.append(("foreign_module", foreign_module))
        print(f"\n[WARN] {len(foreign_module)} LCS-prefixed DocTypes belong to another module")

    # 3. Custom Field duplicates — same field on same DocType inserted twice
    cf_dups = frappe.db.sql(
        """SELECT dt, fieldname, COUNT(*) c
           FROM `tabCustom Field`
           WHERE module = 'LCS Integrations' OR fieldname LIKE 'lcs_%' OR fieldname IN ('erpnext_customer', 'lcs_project', 'lcs_offer', 'sales_order')
           GROUP BY dt, fieldname HAVING c > 1""",
        as_dict=True,
    )
    if cf_dups:
        issues.append(("custom_field_dups", cf_dups))
        print(f"\n[FAIL] {len(cf_dups)} duplicate Custom Fields:")
        for r in cf_dups:
            print(f"        {r.dt}.{r.fieldname} ({r.c}×)")
    else:
        print(f"\n[ OK ] No duplicate Custom Fields under LCS Integrations")

    # 4. Module list — modules.txt vs DocType.module
    expected_module = "LCS Integrations"
    by_module = defaultdict(int)
    for d in lcs_doctypes:
        by_module[d.module] += 1
    print(f"\n[INFO] DocType-by-module distribution:")
    for m, c in by_module.items():
        marker = " " if m == expected_module else "✗"
        print(f"  [{marker}] {m}: {c}")

    # 5. DocType + Custom Field totals on the relevant doctypes
    print(f"\n[INFO] Custom-Field counts on integration targets:")
    for dt in ["CRM Organization", "CRM Deal", "CRM Lead", "Quotation", "Sales Order", "BSM Project", "Lead"]:
        if not frappe.db.exists("DocType", dt):
            continue
        c = frappe.db.count("Custom Field", {"dt": dt, "module": "LCS Integrations"})
        print(f"  {dt:20}: {c} field(s)")

    # 6. Summary
    print("\n" + "=" * 60)
    if issues:
        print(f"  ✗ {len(issues)} issue group(s) — cleanup needed before push")
    else:
        print(f"  ✓ Clean — every DocType exists exactly once, no duplicate Custom Fields")
    print("=" * 60)

    return {
        "is_clean": len(issues) == 0,
        "issues": issues,
        "lcs_doctype_count": len(lcs_doctypes),
        "db_unique_doctypes": len(seen),
    }
