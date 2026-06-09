"""Side-by-side schema comparison: LCS Project vs ERPNext Project."""

import frappe


def run():
    print("\n=== LCS Project vs ERPNext Project — schema diff ===\n")

    if not frappe.db.exists("DocType", "Project"):
        print("[FAIL] ERPNext Project not installed — comparison aborted")
        return

    lcs = {f.fieldname: (f.fieldtype, f.options or "") for f in frappe.get_meta("LCS Project").fields}
    erp = {f.fieldname: (f.fieldtype, f.options or "") for f in frappe.get_meta("Project").fields}

    common = sorted(set(lcs) & set(erp))
    only_lcs = sorted(set(lcs) - set(erp))
    only_erp = sorted(set(erp) - set(lcs))

    print(f"  Total fields: LCS={len(lcs)}  ERPNext={len(erp)}")
    print(f"  Common fieldnames: {len(common)}")
    print(f"  LCS-only:    {len(only_lcs)}")
    print(f"  ERPNext-only:{len(only_erp)}")

    print("\n─── Fields with same name, possibly redundant ───")
    for fn in common:
        ltype, lopts = lcs[fn]
        etype, eopts = erp[fn]
        same_type = ltype == etype and lopts == eopts
        marker = "==" if same_type else "≠"
        print(f"  [{marker}] {fn:25}  LCS:{ltype}({lopts}) {' ' if same_type else '↔'} ERPNext:{etype}({eopts})")

    print("\n─── LCS-only fields (LCS-specific value) ───")
    for fn in only_lcs:
        t, o = lcs[fn]
        print(f"  · {fn:25}  {t}{f' → {o}' if o else ''}")

    print("\n─── ERPNext-only fields (we'd inherit by switching) ───")
    important = [
        "tasks", "users", "estimated_costing", "total_billed_amount",
        "total_consumed_material_cost", "actual_start_date", "actual_end_date",
        "expected_start_date", "expected_end_date", "percent_complete",
        "gross_margin", "project_template", "department",
    ]
    for fn in important:
        if fn in erp:
            t, o = erp[fn]
            print(f"  ★ {fn:32}  {t}{f' → {o}' if o else ''}")
    print("  (truncated — full list in DB)")

    return {
        "common": len(common),
        "lcs_only": len(only_lcs),
        "erp_only": len(only_erp),
    }
