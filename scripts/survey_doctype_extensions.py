"""Print every Custom Field / Property Setter / Client Script /
Server Script that is NOT bound to a CRM doctype and was NOT
shipped by an installed app (is_system_generated = 0).

Run via:
    bench --site lcs.local execute \\
        pilanda_audit.survey_doctype_extensions.survey_doctype_extensions
or copy this script into /tmp and feed it to bench's exec.

Read-only — only prints; no deletes here.
"""
from __future__ import annotations

import frappe


def crm_doctypes() -> set[str]:
    """All DocTypes that live in the `crm` app — these must be
    preserved when the user asks to delete "non-CRM" customisations.
    """
    return {
        r["name"]
        for r in frappe.get_all(
            "DocType",
            filters={"module": ["in", _crm_modules()]},
            fields=["name"],
            limit=0,
        )
    }


def _crm_modules() -> list[str]:
    return [
        r["name"]
        for r in frappe.get_all("Module Def", filters={"app_name": "crm"}, fields=["name"], limit=0)
    ]


def survey_doctype_extensions() -> None:
    crm = crm_doctypes()
    print(f"CRM doctypes (kept): {len(crm)}")
    print()

    # Custom Fields ---------------------------------------------------
    cfs = frappe.get_all(
        "Custom Field",
        fields=["name", "dt", "fieldname", "label", "fieldtype", "module", "is_system_generated", "owner"],
        limit=0,
    )
    user_cfs = [
        c for c in cfs
        if c["dt"] not in crm and not int(c.get("is_system_generated") or 0)
    ]
    print(f"=== Custom Fields outside CRM, user-added: {len(user_cfs)} ===")
    by_dt: dict[str, list] = {}
    for c in user_cfs:
        by_dt.setdefault(c["dt"], []).append(c)
    for dt, rows in sorted(by_dt.items()):
        print(f"  {dt:40s} ({len(rows)})  -> {', '.join(r['fieldname'] for r in rows[:6])}{' …' if len(rows) > 6 else ''}")
    print()

    # Property Setters -----------------------------------------------
    ps = frappe.get_all(
        "Property Setter",
        fields=["name", "doc_type", "field_name", "property", "is_system_generated", "owner"],
        limit=0,
    )
    user_ps = [
        p for p in ps
        if p["doc_type"] not in crm and not int(p.get("is_system_generated") or 0)
    ]
    print(f"=== Property Setters outside CRM, user-added: {len(user_ps)} ===")
    by_dt2: dict[str, list] = {}
    for p in user_ps:
        by_dt2.setdefault(p["doc_type"], []).append(p)
    for dt, rows in sorted(by_dt2.items()):
        names = sorted({f"{r['field_name']}.{r['property']}" if r['field_name'] else r['property'] for r in rows})
        print(f"  {dt:40s} ({len(rows)})  -> {', '.join(names[:6])}{' …' if len(names) > 6 else ''}")
    print()

    # Client Scripts -------------------------------------------------
    cs = frappe.get_all(
        "Client Script",
        fields=["name", "dt", "view", "enabled", "owner"],
        limit=0,
    )
    user_cs = [c for c in cs if c["dt"] not in crm]
    print(f"=== Client Scripts outside CRM: {len(user_cs)} ===")
    for c in user_cs:
        print(f"  {c['dt']:40s}  view={c['view']:10s}  enabled={c['enabled']}  name={c['name']}")
    print()

    # Server Scripts -------------------------------------------------
    try:
        ss = frappe.get_all(
            "Server Script",
            fields=["name", "script_type", "reference_doctype", "doctype_event", "disabled", "owner"],
            limit=0,
        )
        user_ss = [s for s in ss if (s.get("reference_doctype") or "") not in crm]
        print(f"=== Server Scripts outside CRM: {len(user_ss)} ===")
        for s in user_ss:
            ref = s.get("reference_doctype") or "(none)"
            print(f"  {ref:40s}  type={s['script_type']:12s}  event={s.get('doctype_event','-')}  name={s['name']}")
    except Exception as e:  # noqa: BLE001
        print(f"(server script enumeration skipped: {e})")
    print()

    print("Run delete_doctype_extensions.py to actually remove them.")
