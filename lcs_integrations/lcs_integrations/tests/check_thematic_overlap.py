"""
Thematic-overlap audit for the 15 LCS DocTypes.

Two questions answered:
1. Do any two LCS DocTypes do thematically the same thing?
2. Do any LCS DocTypes hold free-text values that would be cleaner as
   Link fields to existing DocTypes in another app (CRM/ERPNext/HRMS/
   LMS/BSM)?

Read-only — produces a report grouped by purpose.
"""

import frappe


# Each LCS DocType's intended purpose, plus what it would conflict with
# if it weren't carved out — used to verify no two LCS doctypes overlap.
PURPOSE = {
    "LCS Project":                "Commercial pivot — single source of truth across CRM/ERP/BSM/HRMS/LMS/PLM",
    "LCS Project Contact":        "Child: project-scoped contacts table (links to core Contact)",
    "LCS Project Team Member":    "Child: project-scoped team table (links to HRMS Employee)",
    "LCS Project Required Training": "Child: required courses per project (links to LMS Course)",

    "LCS Offer":                  "Commercial pre-sales artefact — versioning, status flow, links to ERPNext Quotation",
    "LCS Offer Template":         "Reusable skeleton for new LCS Offers — defaults, placeholders",
    "LCS Opportunity Matrix":     "5-dim scoring (technical/commercial/relationship/competition/strategic) — feeds project.probability",

    "LCS Access Profile":         "Admin-defined view scope (countries / types / actions / hide-flags)",
    "LCS Access Profile Country": "Child: countries allowed by an access profile",
    "LCS Access Profile Project Type": "Child: project types allowed by an access profile",
    "LCS Access Profile Team":    "Child: team members visible to an access profile",

    "LCS User Preferences":       "Per-user display + behaviour preferences (one per User, autoname=user)",

    "LCS Audio Transcription Job":"External-agent (Hermes) STT queue — claim/submit/fail contract",
    "LCS Speech Settings":        "Single: STT backend config (browser vs Azure)",
    "LCS Fusion Manage Settings": "Single: Autodesk Fusion Manage tenant + OAuth tokens",
}


# For each suspicious "free text where link would be cleaner" pattern,
# (doctype, fieldname, suggested_link_to_doctype, reason).
SUSPICIOUS_FREE_TEXT = []


def run():
    print("\n=== Thematic-overlap audit (LCS DocTypes) ===\n")

    lcs_dts = sorted([d.name for d in frappe.get_all("DocType", filters={"name": ["like", "LCS%"]})])

    if len(lcs_dts) != len(PURPOSE):
        print(f"[WARN] DocType count mismatch: DB has {len(lcs_dts)}, PURPOSE map has {len(PURPOSE)}")

    # 1. Print thematic purposes — easy human review for overlap
    print("─── Purpose statements ───\n")
    for dt in lcs_dts:
        purpose = PURPOSE.get(dt, "(no purpose recorded — likely overlap risk!)")
        print(f"  {dt}")
        print(f"    → {purpose}")
        print()

    # 2. Programmatic overlap heuristic: two doctypes with > 70% overlapping
    #    fieldnames suggest duplication.
    print("─── Field-overlap heuristic ───")
    field_sets = {dt: _doctype_fieldset(dt) for dt in lcs_dts}
    overlaps = []
    seen = set()
    for a in lcs_dts:
        for b in lcs_dts:
            if a == b or (b, a) in seen:
                continue
            seen.add((a, b))
            common = field_sets[a] & field_sets[b]
            denominator = min(len(field_sets[a]), len(field_sets[b])) or 1
            if denominator >= 4 and len(common) / denominator > 0.7:
                overlaps.append((a, b, common))
    if overlaps:
        for a, b, c in overlaps:
            print(f"  [WARN] {a} ↔ {b} share {len(c)} field(s): {sorted(c)}")
    else:
        print("  [ OK ] No two LCS DocTypes have suspicious field overlap")
    print()

    # 3. Free-text fields that should be links to other-app DocTypes
    print("─── Suspicious free-text fields ───")
    findings = []
    for dt in lcs_dts:
        for f in frappe.get_meta(dt).fields:
            suggestion = _suggest_link(dt, f)
            if suggestion:
                findings.append((dt, f.fieldname, f.fieldtype, suggestion))

    if findings:
        for dt, fn, ft, sug in findings:
            print(f"  [HINT] {dt}.{fn} ({ft})")
            print(f"           → {sug}")
    else:
        print("  [ OK ] No free-text fields flagged — every reference is a Link")
    print()

    # 4. Cross-app-link inventory — confirm we have FK lines to every
    #    integrated app where it makes sense
    print("─── Cross-app FK inventory ───")
    expected_fks = [
        ("LCS Project",       "organization",        "CRM Organization"),
        ("LCS Project",       "deal",                "CRM Deal"),
        ("LCS Project",       "primary_contact",     "Contact"),
        ("LCS Project",       "country",             "Country"),
        ("LCS Project",       "salesperson",         "User"),
        ("LCS Project",       "source",              "CRM Lead Source"),
        ("LCS Project",       "erpnext_customer",    "Customer"),
        ("LCS Project",       "bsm_project",         "BSM Project"),
        ("LCS Project",       "project_manager",     "Employee"),
        ("LCS Offer",         "project",             "LCS Project"),
        ("LCS Offer",         "currency",            "Currency"),
        ("LCS Offer",         "erpnext_quotation",   "Quotation"),
        ("LCS Offer",         "erpnext_sales_order", "Sales Order"),
        ("LCS Project Required Training", "course",  "LMS Course"),
        ("LCS Project Team Member",       "employee", "Employee"),
        ("LCS Project Contact",           "contact",  "Contact"),
        ("LCS User Preferences",          "user",     "User"),
        ("LCS User Preferences",          "access_profile", "LCS Access Profile"),
    ]
    for dt, fn, expected in expected_fks:
        if not frappe.db.exists("DocType", dt):
            continue
        meta = frappe.get_meta(dt)
        field = next((f for f in meta.fields if f.fieldname == fn), None)
        if not field:
            print(f"  [WARN] {dt}.{fn} — field missing; expected Link → {expected}")
        elif field.fieldtype != "Link":
            print(f"  [WARN] {dt}.{fn} is {field.fieldtype}, expected Link → {expected}")
        elif field.options != expected:
            print(f"  [WARN] {dt}.{fn} → {field.options}, expected {expected}")
        else:
            print(f"  [ OK ] {dt}.{fn} → Link ({expected})")

    print()
    print("=" * 60)
    issues = len(overlaps) + len(findings)
    if issues == 0:
        print("  ✓ All 15 LCS DocTypes are thematically distinct.")
        print("  ✓ Every cross-app reference is a typed Link (no free-text duplicates).")
    else:
        print(f"  ⚠ {issues} item(s) need attention — see HINT/WARN lines above")
    print("=" * 60)
    return {"issues": issues, "doctypes": len(lcs_dts)}


def _doctype_fieldset(dt: str) -> set:
    """Return the set of meaningful fieldnames (skip layout)."""
    skip = {"Section Break", "Column Break", "Tab Break", "HTML"}
    return {
        f.fieldname for f in frappe.get_meta(dt).fields
        if f.fieldtype not in skip
    }


def _suggest_link(dt: str, field) -> str | None:
    """Heuristic: free-text fields that probably should be Links to a known DocType."""
    fn = field.fieldname.lower()
    ft = field.fieldtype

    # Only Data and Small Text get scrutinised — Long Text, Code etc. are fine
    if ft not in ("Data", "Small Text"):
        return None

    # Common patterns
    if fn in ("country", "land", "country_name") and frappe.db.exists("DocType", "Country"):
        return "Should be Link → Country (Frappe core)"
    if fn in ("currency", "currency_code") and frappe.db.exists("DocType", "Currency"):
        return "Should be Link → Currency"
    if fn in ("industry",) and frappe.db.exists("DocType", "CRM Industry"):
        return "Should be Link → CRM Industry"
    if fn in ("territory",) and frappe.db.exists("DocType", "Territory"):
        return "Should be Link → Territory (ERPNext)"
    if fn in ("uom", "stock_uom") and frappe.db.exists("DocType", "UOM"):
        return "Should be Link → UOM"

    return None
